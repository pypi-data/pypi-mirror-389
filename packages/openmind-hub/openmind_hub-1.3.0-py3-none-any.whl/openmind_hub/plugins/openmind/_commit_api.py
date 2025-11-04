# Copyright (c) 2024 Huawei Technologies Co., Ltd.
#
# openMind is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
#
# Note: Part of the implementation is borrowed from huggingface.
import base64
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
import gc
import io
import itertools
import os
from pathlib import Path, PurePosixPath
from typing import (
    BinaryIO,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from tqdm.contrib.concurrent import thread_map

from .constants import DEFAULT_REQUEST_TIMEOUT, ENDPOINT, GIT_LFS_SPE, BIG_FILE_SIZE
from .lfs import UploadInfo, lfs_upload, post_lfs_batch_info
from .utils import OmHubHTTPError, build_om_headers, om_raise_for_status
from .utils._http import get_session
from .utils._validators import is_sensitive_path
from .utils.logging import get_logger, replace_invalid_characters
from .utils.tqdm_hub import tqdm_stream_file
from .utils.tqdm_hub import Tqdm as om_tqdm

T = TypeVar("T")
UploadMode = Literal["lfs", "regular"]
logger = get_logger(__name__)


@dataclass
class CommitOperationDelete:
    """
    Data structure holding necessary info to delete a file or a folder from a repository
    on the Hub.

    Args:
        path_in_repo (`str`):
            Relative filepath in the repo, for example: `"checkpoints/1fec34a/weights.bin"`
            for a file or `"checkpoints/1fec34a/"` for a folder.
        is_folder (`bool` or `Literal["auto"]`, *optional*)
            Whether the Delete Operation applies to a folder or not. If "auto", the path
            type is guessed automatically by looking if path ends with
            a "/" (folder) or not (file). To explicitly set the path type, you can set
            `is_folder=True` or `is_folder=False`.
    """

    path_in_repo: str
    is_folder: Union[bool, Literal["auto"]] = "auto"

    def __post_init__(self):
        self.path_in_repo = _validate_path_in_repo(self.path_in_repo)

        if self.is_folder == "auto":
            self.is_folder = self.path_in_repo.endswith("/")
        if not isinstance(self.is_folder, bool):
            error_msg = (
                f"Wrong value for `is_folder`. Must be one of [`True`, `False`, `'auto'`]. Got '{self.is_folder}'."
            )
            raise ValueError(replace_invalid_characters(error_msg))


@dataclass
class CommitOperationCopy:
    """
    Data structure holding necessary info to copy a file in a repository on the Hub.

    Limitations:
      - Only LFS files can be copied. To copy a regular file, you need to download it locally and re-upload it
      - Cross-repository copies are not supported.

    Note: you can combine a [`CommitOperationCopy`] and a [`CommitOperationDelete`] to rename an LFS file on the Hub.

    Args:
        src_path_in_repo (`str`):
            Relative filepath in the repo of the file to be copied, e.g. `"checkpoints/1fec34a/weights.bin"`.
        path_in_repo (`str`):
            Relative filepath in the repo where to copy the file, e.g. `"checkpoints/1fec34a/weights_copy.bin"`.
        src_revision (`str`, *optional*):
            The git revision of the file to be copied. Can be any valid git revision.
            Default to the target commit revision.
    """

    src_path_in_repo: str
    path_in_repo: str
    src_revision: Optional[str] = None

    def __post_init__(self):
        self.src_path_in_repo = _validate_path_in_repo(self.src_path_in_repo)
        self.path_in_repo = _validate_path_in_repo(self.path_in_repo)


@dataclass
class CommitOperationAdd:
    """
    Data structure holding necessary info to upload a file to a repository on the Hub.

    Args:
        path_in_repo (`str`):
            Relative filepath in the repo, for example: `"checkpoints/1fec34a/weights.bin"`
        path_or_fileobj (`str`, `Path`, `bytes`, or `BinaryIO`):
            Either:
            - a path to a local file (as `str` or `pathlib.Path`) to upload
            - a buffer of bytes (`bytes`) holding the content of the file to upload
            - a "file object" (subclass of `io.BufferedIOBase`), typically obtained
                with `open(path, "rb")`. It must support `seek()` and `tell()` methods.

    Raises:
        [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If `path_or_fileobj` is not one of `str`, `Path`, `bytes` or `io.BufferedIOBase`.
        [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If `path_or_fileobj` is a `str` or `Path` but not a path to an existing file.
        [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If `path_or_fileobj` is a `io.BufferedIOBase` but it doesn't support both
            `seek()` and `tell()`.
    """

    path_in_repo: str
    path_or_fileobj: Union[str, Path, bytes, BinaryIO]
    upload_info: UploadInfo = field(init=False, repr=False)

    # Internal attributes
    upload_mode: Optional[UploadMode] = field(
        init=False, repr=False, default=None
    )  # set to "lfs" or "regular" once known
    is_uploaded: bool = field(
        init=False, repr=False, default=False
    )  # set to True once the file has been uploaded as LFS
    is_committed: bool = field(init=False, repr=False, default=False)  # set to True once the file has been committed

    def __post_init__(self) -> None:
        """Validates `path_or_fileobj` and compute `upload_info`."""
        self.path_in_repo = _validate_path_in_repo(self.path_in_repo)

        # Validate `path_or_fileobj` value
        if isinstance(self.path_or_fileobj, Path):
            self.path_or_fileobj = str(self.path_or_fileobj)
            is_sensitive_path(self.path_or_fileobj)

        if isinstance(self.path_or_fileobj, str):
            path_or_fileobj = os.path.normpath(os.path.expanduser(self.path_or_fileobj))
            is_sensitive_path(self.path_or_fileobj)
            if not os.path.isfile(path_or_fileobj):
                error_msg = f"Provided path: '{path_or_fileobj}' is not a file on the local file system"
                raise ValueError(replace_invalid_characters(error_msg))
        elif not isinstance(self.path_or_fileobj, (io.BufferedIOBase, bytes)):
            raise ValueError(
                "path_or_fileobj must be either an instance of str, bytes or"
                " io.BufferedIOBase. If you passed a file-like object, make sure it is"
                " in binary mode."
            )
        if isinstance(self.path_or_fileobj, io.BufferedIOBase):
            try:
                self.path_or_fileobj.tell()
                self.path_or_fileobj.seek(0, os.SEEK_CUR)
            except (OSError, AttributeError) as exc:
                raise ValueError(
                    "path_or_fileobj is a file-like object but does not implement seek() and tell()"
                ) from exc

        # Compute "upload_info" attribute
        if isinstance(self.path_or_fileobj, str):
            self.upload_info = UploadInfo.from_path(self.path_or_fileobj)
        elif isinstance(self.path_or_fileobj, bytes):
            self.upload_info = UploadInfo.from_bytes(self.path_or_fileobj)
        else:
            self.upload_info = UploadInfo.from_fileobj(self.path_or_fileobj)

    @contextmanager
    def as_file(self, with_tqdm: bool = False) -> Iterator[BinaryIO]:
        if isinstance(self.path_or_fileobj, str) or isinstance(self.path_or_fileobj, Path):
            if with_tqdm:
                with tqdm_stream_file(self.path_or_fileobj) as file:
                    yield file
            else:
                with open(self.path_or_fileobj, "rb") as file:
                    yield file
        elif isinstance(self.path_or_fileobj, bytes):
            yield io.BytesIO(self.path_or_fileobj)
        elif isinstance(self.path_or_fileobj, io.BufferedIOBase):
            prev_pos = self.path_or_fileobj.tell()
            yield self.path_or_fileobj
            self.path_or_fileobj.seek(prev_pos, io.SEEK_SET)
        else:
            error_msg = f"Unsupported file object type: {type(self.path_or_fileobj)}"
            raise TypeError(replace_invalid_characters(error_msg))

    def b64content(self) -> bytes:
        """
        Returns the base64-encoded content of `path_or_fileobj` as bytes.
        Only used in common file(not lfs).

        Returns:
            bytes: Base64-encoded content.
        """
        with self.as_file() as file:
            return base64.b64encode(file.read(BIG_FILE_SIZE))


CommitOperation = Union[CommitOperationAdd, CommitOperationDelete]


def _warn_on_overwriting_operations(operations: List[CommitOperation]) -> None:
    """
    Warn user when a list of operations is expected to overwrite itself in a single
    commit.

    Rules:
    - If a filepath is updated by multiple `CommitOperationAdd` operations, a warning
      message is triggered.
    - If a filepath is updated at least once by a `CommitOperationAdd` and then deleted
      by a `CommitOperationDelete`, a warning is triggered.
    - If a `CommitOperationDelete` deletes a filepath that is then updated by a
      `CommitOperationAdd`, no warning is triggered. This is usually useless (no need to
      delete before upload) but can happen if a user deletes an entire folder and then
      add new files to it.
    """
    nb_additions_per_path: Dict[str, int] = defaultdict(int)
    for operation in operations:
        path_in_repo = operation.path_in_repo
        if isinstance(operation, CommitOperationAdd):
            if nb_additions_per_path[path_in_repo] > 0:
                logger.warning(
                    "About to update multiple times the same file in the same commit:"
                    f" '{path_in_repo}'. This can cause undesired inconsistencies in"
                    " your repo."
                )
            nb_additions_per_path[path_in_repo] += 1
            for parent in PurePosixPath(path_in_repo).parents:
                # Also keep track of number of updated files per folder
                # => warns if deleting a folder overwrite some contained files
                nb_additions_per_path[str(parent)] += 1
        if isinstance(operation, CommitOperationDelete):
            if nb_additions_per_path[str(PurePosixPath(path_in_repo))] > 0:
                if operation.is_folder:
                    logger.warning(
                        "About to delete a folder containing files that have just been"
                        f" updated within the same commit: '{path_in_repo}'. This can"
                        " cause undesired inconsistencies in your repo."
                    )
                else:
                    logger.warning(
                        "About to delete a file that have just been updated within the"
                        f" same commit: '{path_in_repo}'. This can cause undesired"
                        " inconsistencies in your repo."
                    )


def chunk_iterable(iterable: Iterable[T], chunk_size: int) -> Iterable[Iterable[T]]:
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("`chunk_size` must be a strictly positive integer (>0).")

    iterator = iter(iterable)
    while True:
        try:
            next_item = next(iterator)
        except StopIteration:
            return
        yield itertools.chain((next_item,), itertools.islice(iterator, chunk_size - 1))


def _upload_lfs_files(
    *,
    additions: List[CommitOperationAdd],
    repo_id: str,
    token: Optional[str],
    endpoint: Optional[str] = None,
    num_threads: int = 5,
):
    # Step 1: retrieve upload instructions from the LFS batch endpoint.
    #         Upload instructions are retrieved by chunk of 100 files to avoid reaching
    #         the payload limit.
    batch_actions: List[Dict] = []
    for chunk in chunk_iterable(additions, chunk_size=100):
        batch_actions_chunk, batch_errors_chunk = post_lfs_batch_info(
            upload_infos=[op.upload_info for op in chunk],
            token=token,
            repo_id=repo_id,
            endpoint=endpoint,
        )

        # If at least 1 error, we do not retrieve information for other chunks
        if batch_errors_chunk:
            message = replace_invalid_characters(
                "\n".join(
                    [
                        f'Encountered error for file with OID {err.get("oid")}: `{err.get("error", {}).get("message")}'
                        for err in batch_errors_chunk
                    ]
                )
            )
            raise ValueError(f"LFS batch endpoint returned errors:\n{message}")

        batch_actions += batch_actions_chunk

    del token
    gc.collect()
    oid2addop = {add_op.upload_info.sha256.hex(): add_op for add_op in additions}

    # Step 2: ignore files that have already been uploaded
    filtered_actions = []
    for action in batch_actions:
        if not action.get("actions") and action.get("oid"):
            logger.debug(
                f"Content of file {oid2addop[action.get('oid')].path_in_repo} is already"
                " present upstream - skipping upload."
            )
            return
        else:
            filtered_actions.append(action)

    # This means all the file slices have been uploaded to OBS.
    if filtered_actions and "parts" not in filtered_actions[0].get("actions"):
        return

    # Step 3: upload files concurrently according to these instructions
    def _wrapped_lfs_upload(batch_action) -> None:
        try:
            oid = batch_action.get("oid")
            operation = oid2addop.get(oid)
            if not operation:
                raise ValueError(replace_invalid_characters(f"unknow oid {oid} for upload operation"))
            lfs_upload(operation=operation, lfs_batch_action=batch_action)
        except OmHubHTTPError as exc:
            raise RuntimeError("Error while uploading to the Hub. Please try again.") from exc

    if not filtered_actions:
        logger.debug("No LFS files to upload.")
        return
    if len(filtered_actions) == 1:
        _wrapped_lfs_upload(filtered_actions[0])
    else:
        thread_map(
            _wrapped_lfs_upload,
            filtered_actions,
            desc=f"Upload {len(filtered_actions)} LFS files",
            max_workers=num_threads,
            tqdm_class=om_tqdm,
        )


def _validate_path_in_repo(path_in_repo: str) -> str:
    # Validate `path_in_repo` value to prevent a server-side issue
    if path_in_repo.startswith("/"):
        path_in_repo = path_in_repo[1:]
    if path_in_repo == "." or path_in_repo == ".." or path_in_repo.startswith("../"):
        error_msg = f"Invalid `path_in_repo` in CommitOperation: '{path_in_repo}'"
        raise ValueError(replace_invalid_characters(error_msg))
    if path_in_repo.startswith("./"):
        path_in_repo = path_in_repo[2:]
    if any(part == ".git" for part in path_in_repo.split("/")):
        error_msg = (
            "Invalid `path_in_repo` in CommitOperation: cannot update files under a '.git/' folder "
            f"(path:'{path_in_repo}')."
        )
        raise ValueError(replace_invalid_characters(error_msg))
    return path_in_repo


def build_pointer_file(operation):
    pointer_inf = operation.upload_info
    sha256_raw = operation.upload_info.sha256.hex()
    size = pointer_inf.size
    raw_pointer = f"{GIT_LFS_SPE}\noid sha256:{sha256_raw}\nsize {size}"
    return raw_pointer


def _prepare_commit_payload(
    operations: Iterable[CommitOperation],
    commit_message: Optional[str] = None,
    revision: Optional[str] = None,
):
    result_payload = {}
    file_list = []
    for operation in operations:
        if isinstance(operation, CommitOperationAdd) and operation.upload_mode == "lfs":
            lfs_file_infor = {
                "operation": "create",
                "content": base64.b64encode(build_pointer_file(operation).encode("utf-8")).decode("utf-8"),
                "path": operation.path_in_repo,
            }
            file_list.append(lfs_file_infor)
        elif isinstance(operation, CommitOperationAdd):
            regular_file_infor = {
                "operation": "create",
                "content": operation.b64content().decode(),
                "path": operation.path_in_repo,
            }
            file_list.append(regular_file_infor)
        elif isinstance(operation, CommitOperationDelete):
            delete_file_infor = {
                "operation": "delete",
                "path": operation.path_in_repo,
            }
            file_list.append(delete_file_infor)
    result_payload["files"] = file_list
    if revision:
        result_payload["ref"] = revision
    if commit_message:
        result_payload["title"] = commit_message
    return result_payload


def _fetch_upload_modes(
    additions: List[CommitOperationAdd],
    repo_id: str,
    token: Optional[str],
    revision: Optional[str],
    endpoint: Optional[str] = None,
) -> None:
    """
    request backend to determine upload modes:
        1. Regular upload
        2. LFS upload
    """

    endpoint = endpoint or ENDPOINT
    headers = build_om_headers(token=token)

    upload_modes: Dict[str, UploadMode] = {}

    for chunk in chunk_iterable(additions, 100):
        payload: Dict = {
            "branch": revision,
            "files": [
                {
                    "path": op.path_in_repo,
                    "size": op.upload_info.size,
                    "sha": op.upload_info.sha256.hex(),
                }
                for op in chunk
            ],
        }

        request_url = f"{endpoint}/api/v1/file/{repo_id}/pre_upload"

        logger.info("_fetch_upload_modes send HTTPS request")
        resp = get_session().post(
            request_url,
            json=payload,
            headers=headers,
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

        om_raise_for_status(resp)
        preupload_info = resp.json().get("data")
        if not preupload_info or not isinstance(preupload_info, dict):
            raise ValueError("response is not correct.")
        files = preupload_info.get("files")
        if not files or not isinstance(files, list):
            raise ValueError("response is not correct.")
        upload_modes.update(**{file.get("path"): file.get("type") for file in files})

    del token, headers
    gc.collect()

    # Set upload mode for each addition operation
    for addition in additions:
        upload_mode = upload_modes.get(addition.path_in_repo, None)
        if not upload_mode:
            error_msg = f"Unknow file mode for {addition.path_in_repo}. Please check the file and retry."
            raise ValueError(replace_invalid_characters(error_msg))
        addition.upload_mode = upload_mode

    for addition in additions:
        if addition.upload_info.size == 0:
            addition.upload_mode = "regular"
