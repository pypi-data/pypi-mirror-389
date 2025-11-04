# Copyright 2019-present, the HuggingFace Inc. team.
# Copyright (c) Huawei Technologies Co., Ltd. 2023-2023, All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from contextlib import AbstractContextManager
import gc
import io
import os
from dataclasses import dataclass
from os.path import getsize
from typing import BinaryIO, Dict, Iterable, List, TypedDict, TYPE_CHECKING, Optional, Tuple

from .constants import (
    DEFAULT_REQUEST_TIMEOUT,
    ENDPOINT,
    MULTIUPLOAD_SIZE,
    ONE_MEGABYTE,
    MAX_LFS_SIZE,
    sha256,
)
from .utils import om_raise_for_status, OMValidationError
from .utils.logging import replace_invalid_characters, get_logger
from .utils._http import get_session, http_backoff


logger = get_logger(__name__)

if TYPE_CHECKING:
    from ._commit_api import CommitOperationAdd


@dataclass
class UploadInfo:
    """
    Dataclass holding required information to determine whether a blob
    should be uploaded to the hub using the LFS protocol or the regular protocol

    Args:
        sha256 (`bytes`):
            SHA256 hash of the blob
        size (`int`):
            Size in bytes of the blob
        sample (`bytes`):
            First 512 bytes of the blob
    """

    sha256: bytes
    size: int
    sample: bytes

    @classmethod
    def from_path(cls, path: str):
        size = getsize(path)
        if size > MAX_LFS_SIZE:
            raise OMValidationError(f"{path} size should be less than {MAX_LFS_SIZE}")
        with io.open(path, "rb") as file:
            sample = file.read(512)
            file.seek(0, io.SEEK_SET)
            sha = sha_fileobj(file)
        return cls(size=size, sha256=sha, sample=sample)

    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) > MAX_LFS_SIZE:
            raise OMValidationError(f"bytes size should be less than {MAX_LFS_SIZE}")
        sha = sha256(data).digest()
        return cls(size=len(data), sample=data[:512], sha256=sha)

    @classmethod
    def from_fileobj(cls, fileobj: BinaryIO):
        sample = fileobj.read(512)
        fileobj.seek(0, io.SEEK_SET)
        sha = sha_fileobj(fileobj)
        size = fileobj.tell()
        if size > MAX_LFS_SIZE:
            raise OMValidationError(f"{fileobj} size should be less than {MAX_LFS_SIZE}")
        fileobj.seek(0, io.SEEK_SET)
        return cls(size=size, sha256=sha, sample=sample)


class SliceFileObj(AbstractContextManager):
    def __init__(self, fileobj: BinaryIO, seek_from: int, read_limit: int):
        # Validate seek_from is a non-negative integer
        if not isinstance(seek_from, int) or seek_from < 0:
            raise ValueError("seek_from must be a non-negative integer")

        # Validate read_limit is a positive integer
        if not isinstance(read_limit, int) or read_limit <= 0:
            raise ValueError("read_limit must be a positive integer")

        self.fileobj = fileobj
        self.seek_from = seek_from
        self.read_limit = read_limit
        self._len = None
        self._previous_position = None

    def __enter__(self):
        self._previous_position = self.fileobj.tell()
        end_of_stream = self.fileobj.seek(0, os.SEEK_END)
        self._len = min(self.read_limit, end_of_stream - self.seek_from)
        # ^^ The actual number of bytes that can be read from the slice
        self.fileobj.seek(self.seek_from, io.SEEK_SET)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fileobj.seek(self._previous_position, io.SEEK_SET)

    def __iter__(self):
        yield self.read(n=4 * ONE_MEGABYTE)

    def read(self, n: int = -1):
        pos = self.tell()
        if pos >= self._len:
            return b""
        remaining_amount = self._len - pos
        data = self.fileobj.read(remaining_amount if n < 0 else min(n, remaining_amount))
        return data

    def tell(self) -> int:
        return self.fileobj.tell() - self.seek_from

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        start = self.seek_from
        end = start + self._len
        if whence in (os.SEEK_SET, os.SEEK_END):
            offset = start + offset if whence == os.SEEK_SET else end + offset
            offset = max(start, min(offset, end))
            whence = os.SEEK_SET
        elif whence == os.SEEK_CUR:
            cur_pos = self.fileobj.tell()
            offset = max(start - cur_pos, min(offset, end - cur_pos))
        else:
            error_msg = f"whence value {whence} is not supported"
            raise ValueError(replace_invalid_characters(error_msg))
        return self.fileobj.seek(offset, whence) - self.seek_from


def post_lfs_batch_info(
    upload_infos: Iterable[UploadInfo],
    token: Optional[str],
    repo_id: str,
    endpoint: Optional[str] = None,
) -> Tuple[list, list]:
    lfs_headers = {
        "Accept": "application/vnd.git-lfs+json",
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
    }
    endpoint = endpoint or ENDPOINT
    batch_url = f"{endpoint}/api/v1/file/{repo_id}/info/lfs/objects/batch"
    payload: Dict = {
        "operation": "upload",
        "transfers": ["basic", "multipart"],
        "objects": [
            {
                "oid": upload.sha256.hex(),
                "size": upload.size,
            }
            for upload in upload_infos
        ],
        "hash_algo": "sha256",
    }

    logger.info("post_lfs_batch_info send HTTPS request")
    resp = get_session().post(
        batch_url,
        headers=lfs_headers,
        json=payload,
        timeout=DEFAULT_REQUEST_TIMEOUT,
    )

    del token, lfs_headers
    gc.collect()

    om_raise_for_status(resp)

    # Uploading Large Files: Slicing and Batching Instructions
    # To facilitate the upload of large files, the file should be segmented into smaller portions. The instructions
    # for the upload process, including slicing details, are contained within the batch_info structure.
    #
    # This structure holds a sequence of instructions for each segment of the file, outlined as follows:
    data = resp.json().get("data")
    if not data or not isinstance(data, dict):
        raise ValueError("post_lfs_batch_info failed, response is not correct.")

    objects = data.get("objects")
    if not isinstance(objects, list):
        raise ValueError("post_lfs_batch_info failed, response is not correct.")
    for info in objects:
        if not isinstance(info, dict):
            raise ValueError("post_lfs_batch_info failed, response is not correct.")
    # return objects
    return (
        [obj for obj in objects if _validate_batch_actions(obj).get("error").get("code") < 300],
        [obj for obj in objects if _validate_batch_actions(obj).get("error").get("code") >= 300],
    )


def lfs_upload(operation: "CommitOperationAdd", lfs_batch_action: Dict) -> None:
    # 0. If LFS file is already present, skip upload
    _validate_batch_actions(lfs_batch_action)
    actions = lfs_batch_action.get("actions")
    if not actions:
        logger.debug(f"Content of file {operation.path_in_repo} is already present upstream - skipping upload")
        return

    # 1. Validate server response, skip the update process if file is already on obs.
    upload_action = actions.get("parts")
    verify_action = actions.get("verify")

    # 2. Upload file
    upload_url_dict = {
        d.get("index"): [d.get("etag", ""), d.get("href", ""), d.get("headers", {})] for d in upload_action
    }
    chunk_size = upload_action[0].get("size", MULTIUPLOAD_SIZE)

    _upload_multi_part(
        operation=operation, chunk_size=chunk_size, upload_url_dict=upload_url_dict, verify_inf=verify_action
    )


def _validate_batch_actions(lfs_batch_actions: dict):
    """validates response from the LFS batch endpoint"""
    if not (isinstance(lfs_batch_actions.get("oid"), str) and isinstance(lfs_batch_actions.get("size"), int)):
        raise ValueError("lfs_batch_actions is improperly formatted")

    lfs_batch_error = lfs_batch_actions.get("error")
    if not lfs_batch_error:
        lfs_batch_actions["error"] = {"code": 200}
    else:
        if not (isinstance(lfs_batch_error, dict) and isinstance(lfs_batch_error.get("code"), int)):
            raise ValueError("lfs_batch_actions error is improperly formatted")
        elif lfs_batch_error.get("code") >= 300:
            # error code is 422 indicates the file size is more than MAX_LFS_SIZE. So that the actions is None.
            return lfs_batch_actions

    upload_action = lfs_batch_actions.get("actions", {}).get("parts")
    # parts is a list of file slice to upload. Unuploaded part has href, while uploaded part has etag.
    if not (
        isinstance(upload_action, list)
        and (isinstance(upload_action[0].get("href"), str) or isinstance(upload_action[0].get("etag"), str))
    ):
        raise ValueError("lfs_batch_actions part is improperly formatted")
    verify_action = lfs_batch_actions.get("actions", {}).get("verify")
    if verify_action and not (isinstance(verify_action, dict) and isinstance(verify_action.get("href"), str)):
        raise ValueError("lfs_batch_actions verify is improperly formatted")
    return lfs_batch_actions


def generate_etag_header(part_upload_url: List) -> Dict:
    etag_header = {"Server": "OBS", "ETag": part_upload_url[0]}
    return etag_header


def _upload_parts_iteratively(operation: "CommitOperationAdd", upload_url_dict: Dict, chunk_size: int) -> List[Dict]:
    headers = []
    with operation.as_file(with_tqdm=True) as fileobj:
        for part_idx, part_upload_url in upload_url_dict.items():
            upload_url = part_upload_url[1]
            upload_headers = part_upload_url[2]
            with SliceFileObj(
                fileobj,
                seek_from=chunk_size * (part_idx - 1),
                read_limit=chunk_size,
            ) as fileobj_slice:
                if upload_url:
                    # upload remaining file chunks to obs
                    part_upload_res = http_backoff(
                        "PUT",
                        upload_url,
                        data=fileobj_slice,
                        headers=upload_headers,
                        retry_on_status_codes=(408, 500, 503),
                    )
                    # When a user uploads the same LFS file, a 404 error occurs because the task_id on the obs side is invalid.
                    # Therefore, 404 error is excluded here
                    if part_upload_res.status_code != 404:
                        om_raise_for_status(part_upload_res)
                    # save etag to header for later verification
                    headers.append(part_upload_res.headers)
                else:
                    # ignore part that have been uploaded
                    fileobj_slice.read()
                    # save etag to header for later verification
                    headers.append(generate_etag_header(part_upload_url))
    return headers


class PayloadPartT(TypedDict):
    index: int
    etag: str


class CompletionPayloadT(TypedDict):
    """Payload that will be sent to the Hub when uploading multipart."""

    upload_id: str
    part_ids: List[PayloadPartT]


def _get_completion_payload(response_headers: List[Dict], oid: str) -> CompletionPayloadT:
    parts: List[PayloadPartT] = []
    for part_number, header in enumerate(response_headers):
        if "ETag" in header:
            etag = header.get("ETag")
        else:
            etag = header.get("etag", "")
        etag = etag.replace(r'"', "")

        parts.append(
            {
                "index": part_number + 1,
                "etag": etag,
            }
        )
    return {"upload_id": oid, "part_ids": parts}


def _upload_multi_part(
    operation: "CommitOperationAdd",
    chunk_size: int,
    upload_url_dict: Dict,
    verify_inf: Dict,
) -> None:
    """
    Uploads file using obs multipart LFS transfer protocol.
    """
    response_headers = _upload_parts_iteratively(
        operation=operation, upload_url_dict=upload_url_dict, chunk_size=chunk_size
    )
    # gitcode probably no verification required
    if not verify_inf:
        return

    # 3. Send completion request
    data = _get_completion_payload(response_headers, operation.upload_info.sha256.hex())
    data["upload_id"] = verify_inf.get("params").get("upload_id")
    logger.info("_upload_multi_part send HTTPS request to verify upload actions")
    r = get_session().post(
        verify_inf.get("href"),
        json=data,
        params=verify_inf.get("params"),
        headers=verify_inf.get("headers"),
    )
    om_raise_for_status(r)


def sha_fileobj(fileobj: BinaryIO, chunk_size: Optional[int] = None) -> bytes:
    """
    Computes the sha256 hash of the given file object, by chunks of size `chunk_size`.

    Args:
        fileobj (file-like object):
            The File object to compute sha256 for, typically obtained with `open(path, "rb")`
        chunk_size (`int`, *optional*):
            The number of bytes to read from `fileobj` at once, defaults to 1MB.

    Returns:
        `bytes`: `fileobj`'s sha256 hash as bytes
    """
    chunk_size = chunk_size if chunk_size else ONE_MEGABYTE

    sha = sha256()
    while True:
        chunk = fileobj.read(chunk_size)
        sha.update(chunk)
        if not chunk:
            break
    return sha.digest()
