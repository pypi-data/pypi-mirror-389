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
import contextlib
import ctypes
import errno
from contextlib import contextmanager
import copy
from dataclasses import dataclass
from functools import partial
import gc
import io
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, BinaryIO, Dict, Generator, Literal, Optional, Union
from urllib.parse import quote, urlencode, urlparse

from filelock import FileLock
import requests

from .constants import (
    sha1,
    sha256,
    BIG_FILE_SIZE,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_REVISION,
    DIR_MODE,
    DOWNLOAD_CHUNK_SIZE,
    ENDPOINT,
    FILE_MODE,
    OM_HUB_CACHE,
    REGEX_COMMIT_HASH,
    REPO_ID_SEPARATOR,
    REPO_TYPES,
    HttpMethodList,
    LFS_REGEX_COMMIT_HASH,
    ONE_MEGABYTE,
    REPO_TYPE_MODEL,
)
from .utils import (
    build_om_headers,
    om_raise_for_status,
    EntryNotFoundError,
    GatedRepoError,
    LocalEntryNotFoundError,
    OmHubHTTPError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)
from .utils.logging import replace_invalid_characters, get_logger
from .utils.tqdm_hub import Tqdm
from .utils._error import FileMetadataError, OMValidationError
from .utils._http import get_session, reset_sessions, CustomCipherAdapter
from .utils._validators import validate_om_hub_args, is_sensitive_path, validate_revision, validate_download_url

_CACHED_NO_EXIST = object()
_CACHED_NO_EXIST_T = Any
_are_symlinks_supported_in_dir: Dict[str, bool] = {}
logger = get_logger(__name__)
HAS_LOGGED_ROOT_WARNING = False
HAS_LOGGED_FILE_MODE_CHECK_WARNING = set()
HAS_CHECKED_REPO_EXISTS = set()


def check_repo_exists(repo_id: str, repo_type: str, token: str, endpoint: str):
    global HAS_CHECKED_REPO_EXISTS
    if (repo_id, repo_type) in HAS_CHECKED_REPO_EXISTS:
        return
    HAS_CHECKED_REPO_EXISTS.add((repo_id, repo_type))
    endpoints = ["openmind.cn", "osinfra.cn", "modelers.cn"]
    endpoint = endpoint or ENDPOINT
    parsed_ep = urlparse(endpoint)
    for ep in endpoints:
        if parsed_ep.hostname.endswith(ep):
            from .om_api import repo_info

            repo_info(repo_id=repo_id, repo_type=repo_type, token=token)
            return


def _to_local_dir(
    path: str,
    local_dir: str,
    relative_filename: str,
    use_symlinks: Union[bool, Literal["auto"]],
) -> str:
    """
    Place a file in a local dir (different from cache_dir).
    Either symlink to blob file in cache or duplicate file
    depending on `use_symlinks` and file size.
    """
    # Using `os.path.abspath` instead of `Path.resolve()` to avoid resolving symlinks
    local_dir_filepath = os.path.join(local_dir, relative_filename)
    os.makedirs(os.path.dirname(local_dir_filepath), mode=0o750, exist_ok=True)

    real_blob_path = os.path.realpath(path)
    # If "auto" (default) copy-paste small files
    # to ease manual editing but symlink big files to save disk
    if use_symlinks == "auto":
        use_symlinks = os.stat(real_blob_path).st_size > BIG_FILE_SIZE
    if use_symlinks:
        _create_symlink(real_blob_path, local_dir_filepath, new_blob=False)
    else:
        shutil.copyfile(real_blob_path, local_dir_filepath)
        logger.info(f"chmod {local_dir_filepath} 0o640")
        os.chmod(local_dir_filepath, mode=0o640)

    return local_dir_filepath


def _normalize_etag(etag: Optional[str]) -> Optional[str]:
    if etag is None:
        return None
    return etag.lstrip("W/").strip('"')


def _int_or_none(value: Optional[str]) -> Optional[int]:
    try:
        return int(value)  # type: ignore
    except (TypeError, ValueError):
        return None


def repo_folder_name(*, repo_id: str, repo_type: str) -> str:
    # remove all `/` occurrences to correctly convert repo to directory name
    parts = [f"{repo_type}s", *repo_id.split("/")]
    return REPO_ID_SEPARATOR.join(parts)


@validate_om_hub_args
def om_hub_url(
    repo_id: str,
    filename: str,
    *,
    subfolder: Optional[str] = None,
    revision: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs,
) -> str:
    """Construct the URL of a file from the given information.

    Args:
        repo_id (`str`):
            A namespace (user or an organization) name and a repo name separated
            by a `/`.
        filename (`str`):
            The name of the file in the repo.
        subfolder (`str`, *optional*):
            An optional value corresponding to a folder inside the repo.
        revision (`str`, *optional*):
            An optional Git revision id which can be a branch name, a tag, or a
            commit hash.
    """

    if subfolder:
        filename = f"{subfolder}/{filename}"
    revision = revision or DEFAULT_REVISION
    url = f"{endpoint or ENDPOINT}/api/v1/file/{repo_id}/{revision}/media/{quote(filename)}"
    return url


@dataclass(frozen=True)
class OmFileMetadata:
    commit_hash: Optional[str]
    etag: Optional[str]
    location: str
    size: Optional[int]


def _download_request_wrapper(
    method: HttpMethodList,
    url: str,
    **params,
) -> requests.Response:
    """Wrapper around requests methods to follow relative redirects if `follow_relative_redirects=True` even when
    `allow_redirection=False`.

    Args:
        method (`str`):
            HTTP method, such as 'GET' or 'HEAD'.
        url (`str`):
            The URL of the resource to fetch.
        **params (`dict`, *optional*):
            Params to pass to `requests.request`.
    """
    session = requests.Session()
    session.mount("https://", CustomCipherAdapter())
    max_retries = 5
    tried = 0
    while True:
        tried += 1
        try:
            response = session.request(method=method, url=url, allow_redirects=False, **params)
            break
        except requests.exceptions.ConnectionError:
            if tried > max_retries:
                raise
            logger.warning("ConnectionError occurred during download. Retrying...")
            time.sleep(1)

    if 300 <= response.status_code <= 399:
        # Download url will be redirected to cdn.
        location = response.headers.get("Location", "")
        validate_download_url(location)
        parsed_target = urlparse(location)
        if parsed_target.hostname:
            return _download_request_wrapper(
                method=method,
                url=location,
                **params,
            )
        else:
            raise OMValidationError("Download url should be redirected but the redirection url is None.")
    return response


@contextlib.contextmanager
def soft_temporary_directory(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    directory: Optional[Union[Path, str]] = None,
    **kwargs,
):
    tmpdir = tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=directory, **kwargs)
    yield tmpdir.name
    import stat

    def _set_write_permission_and_retry(func, path, excinfo):
        logger.info(f"chmod {path} {stat.S_IWRITE} to rm {tmpdir.name}. {excinfo}")
        os.chmod(path, stat.S_IWRITE)
        func(path)

    logger.info(f"rm tmpdir: {tmpdir.name}")
    shutil.rmtree(tmpdir.name, ignore_errors=True, onerror=_set_write_permission_and_retry)
    tmpdir.cleanup()


def are_symlinks_supported(cache_dir: Union[str, Path, None] = None) -> bool:
    cache_dir = cache_dir or OM_HUB_CACHE
    cache_dir = str(Path(cache_dir).expanduser().resolve())  # make it unique

    if cache_dir not in _are_symlinks_supported_in_dir:
        _are_symlinks_supported_in_dir[cache_dir] = True
        os.makedirs(cache_dir, mode=0o750, exist_ok=True)
        with soft_temporary_directory(directory=cache_dir) as tmp_dir:
            src_path = Path(tmp_dir) / "dummy_file_src"
            src_path.touch()
            dst_path = Path(tmp_dir) / "dummy_file_dst"

            # Relative source path as in `_create_symlink``
            relative_src = os.path.relpath(src_path, start=os.path.dirname(dst_path))
            try:
                os.symlink(relative_src, dst_path)
            except OSError:
                _are_symlinks_supported_in_dir[cache_dir] = False

    return _are_symlinks_supported_in_dir[cache_dir]


def check_admin():
    """
    Checks if the current user has ownership of the specified file or directory.
    Raises SystemError if the user is not the owner and is not the root user.

    """
    global HAS_LOGGED_ROOT_WARNING
    if HAS_LOGGED_ROOT_WARNING:
        return

    if os.name == "nt":
        is_root_user = ctypes.windll.shell32.IsUserAnAdmin()
    else:
        is_root_user = os.getuid() == 0

    if is_root_user:
        logger.warning("You are running openMind Hub Client as an Admin user, which is not recommended.")
        HAS_LOGGED_ROOT_WARNING = True


def check_file_mode(file_path):
    """Check if file mode no more than 640, parent dir mode no more than 750."""
    global HAS_LOGGED_FILE_MODE_CHECK_WARNING
    if file_path in HAS_LOGGED_FILE_MODE_CHECK_WARNING:
        return
    if os.name == "nt":
        logger.warning("Cannot check file mode in Windows. Please pay attention to file security.")
        HAS_LOGGED_FILE_MODE_CHECK_WARNING.add(file_path)
        return
    real_file = os.path.realpath(file_path)
    real_mode = oct(os.stat(real_file).st_mode)[-3:]
    for i in range(3):
        if real_mode[i] not in FILE_MODE[i]:
            logger.warning(f"Warning: {real_file} mode is {real_mode}, please pay attention to file security.")
            break
    parent_path = os.path.dirname(real_file)
    parent_mode = oct(os.stat(parent_path).st_mode)[-3:]
    for i in range(1, 3):
        if parent_mode[i] not in DIR_MODE[i]:
            logger.warning(f"Warning: {parent_path} mode is {parent_mode}, please pay attention to file security.")
            break


def _create_symlink(src: str, dst: str, new_blob: bool = False) -> None:
    if os.path.exists(dst) and is_sensitive_path(dst):
        logger.info(replace_invalid_characters(f"remove existed symlink: {dst}"))
        os.remove(dst)

    abs_src = os.path.abspath(os.path.expanduser(src))
    abs_dst = os.path.abspath(os.path.expanduser(dst))
    abs_dst_folder = os.path.dirname(abs_dst)

    # Use relative_dst in priority
    try:
        relative_src = os.path.relpath(abs_src, abs_dst_folder)
    except ValueError:
        # Raised on Windows if src and dst are not on the same volume. This is the case when creating a symlink to a
        # local_dir instead of within the cache directory.
        relative_src = None

    try:
        commonpath = os.path.commonpath([abs_src, abs_dst])
        _support_symlinks = are_symlinks_supported(commonpath)
    except ValueError:
        # Raised if src and dst are not on the same volume. Symlinks will still work on Linux/macOS.
        _support_symlinks = os.name != "nt"
    except PermissionError:
        # Permission error means src and dst are not in the same volume (e.g. destination path has been provided
        # by the user via `local_dir`. Let's test symlink support there)
        _support_symlinks = are_symlinks_supported(abs_dst_folder)
    except OSError as e:
        # OS error (errno=30) means that the commonpath is readonly on Linux/macOS.
        if e.errno == errno.EROFS:
            _support_symlinks = are_symlinks_supported(abs_dst_folder)
        else:
            error_msg = f"{os.path.commonpath([abs_src, abs_dst])} is readonly."
            raise OSError(replace_invalid_characters(error_msg)) from e

    # Symlinks are supported => let's create a symlink.
    if _support_symlinks:
        src_rel_or_abs = relative_src or abs_src
        logger.debug(f"Creating pointer from {src_rel_or_abs} to {abs_dst}")
        try:
            logger.info(f"create symlink: {abs_dst} to {src_rel_or_abs}")
            os.symlink(src_rel_or_abs, abs_dst)
            return
        except FileExistsError as e:
            if os.path.islink(abs_dst) and os.path.realpath(abs_dst) == os.path.realpath(abs_src):
                # `abs_dst` already exists and is a symlink to the `abs_src` blob. It is most likely that the file has
                # been cached twice concurrently (exactly between `os.remove` and `os.symlink`). Do nothing.
                return
            else:
                # Very unlikely to happen. Means a file `dst` has been created exactly between `os.remove` and
                # `os.symlink` and is not a symlink to the `abs_src` blob file. Raise exception.
                error_msg = f"{abs_dst} has been created exactly and is not a symlink to {src_rel_or_abs}."
                raise FileExistsError(replace_invalid_characters(error_msg)) from e
        except PermissionError:
            # Permission error means src and dst are not in the same volume (e.g. download to local dir) and symlink
            # is supported on both volumes but not between them. Let's just make a hard copy in that case.
            logger.warning(
                "Src and dst are not in the same volume and symlink is supported on both volumes but not between them."
                " Hard copy will be made."
            )

    # Symlinks are not supported => let's move or copy the file.
    if new_blob:
        logger.info(f"Symlink not supported. Moving file from {abs_src} to {abs_dst}")
        shutil.move(abs_src, abs_dst)
    else:
        logger.info(f"Symlink not supported. Copying file from {abs_src} to {abs_dst}")
        shutil.copyfile(abs_src, abs_dst)
        logger.info(f"chmod {abs_dst} 0o640")
        os.chmod(abs_dst, mode=0o640)


@validate_om_hub_args
def get_om_file_metadata(
    url: str,
    token: Optional[str] = None,
    proxies: Optional[Dict] = None,
    timeout: Optional[float] = DEFAULT_REQUEST_TIMEOUT,
    **kwargs,
) -> OmFileMetadata:
    # Retrieve metadata
    headers = build_om_headers(token=token)

    logger.info("get_om_file_metadata send HTTPS request")
    r = get_session().get(
        url,
        proxies=proxies,
        timeout=timeout,
        headers=headers,
    )
    om_raise_for_status(r)
    response_data = r.json().get("data")

    if not response_data or not isinstance(response_data, dict):
        raise ValueError("response is not correct.")
    commit_hash = response_data.get("branch_last_commit")
    if not isinstance(commit_hash, str):
        raise ValueError("response is not correct.")
    if not REGEX_COMMIT_HASH.match(commit_hash):
        raise RevisionNotFoundError("Revision was not found.")

    etag = _normalize_etag(response_data.get("etag"))
    if not isinstance(etag, str):
        raise ValueError("response is not correct.")
    if not REGEX_COMMIT_HASH.match(etag) and not LFS_REGEX_COMMIT_HASH.match(etag):
        raise EntryNotFoundError("File etag was wrong.")

    return OmFileMetadata(
        commit_hash=commit_hash,
        etag=etag,
        location=response_data.get("url") or r.request.url,  # type: ignore
        size=_int_or_none(response_data.get("size")),
    )


def _get_pointer_path(storage_folder: str, revision: str, relative_filename: str) -> str:
    # Using `os.path.abspath` instead of `Path.resolve()` to avoid resolving symlinks
    snapshot_path = os.path.join(storage_folder, "snapshots")
    pointer_path = os.path.join(snapshot_path, revision, relative_filename)
    if Path(os.path.abspath(snapshot_path)) not in Path(os.path.abspath(pointer_path)).parents:
        error_msg = (
            "Invalid pointer path: cannot create pointer path in snapshot folder if"
            f" `storage_folder='{storage_folder}'`, `revision='{revision}'` and"
            f" `relative_filename='{relative_filename}'`."
        )
        raise ValueError(replace_invalid_characters(error_msg))
    return pointer_path


def _cache_commit_hash_for_specific_revision(storage_folder: str, revision: str, commit_hash: str) -> None:
    if revision != commit_hash:
        ref_path = Path(storage_folder) / "refs" / revision
        ref_path.parent.mkdir(parents=True, mode=0o750, exist_ok=True)
        if not ref_path.exists() or os.path.getsize(ref_path) >= ONE_MEGABYTE or commit_hash != ref_path.read_text():
            ref_path.write_text(commit_hash)


@validate_om_hub_args
def http_get(
    url: str,
    temp_file: BinaryIO,
    *,
    proxies: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None,
    displayed_filename: Optional[str] = None,
    resume_size: float = 0,
    expected_size: Optional[int] = None,
    _nb_retries: int = 5,
    **kwargs,
):
    if headers is not None and not isinstance(headers, Dict):
        raise TypeError("`headers` should be Dict or None.")
    initial_headers = headers
    headers = copy.deepcopy(headers) or {}
    if resume_size > 0:
        headers["Range"] = "bytes=%d-" % (resume_size,)

    logger.info("http_get send HTTPS request")
    r = _download_request_wrapper(
        method="GET", url=url, stream=True, proxies=proxies, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT
    )
    om_raise_for_status(r)

    content_length = r.headers.get("Content-Length", 0)

    total = resume_size + int(content_length) if content_length else None

    displayed_filename = displayed_filename or url.split("/")[-1]

    # Truncate filename if too long to display
    if len(displayed_filename) > 40:
        displayed_filename = f"(…){displayed_filename[-40:]}"

    # Stream file to buffer
    with Tqdm(
        unit="B",
        unit_scale=True,
        total=total,
        initial=resume_size,
        desc=displayed_filename,
    ) as progress:
        new_resume_size = resume_size
        try:
            for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    chunk_length = len(chunk)
                    progress.update(chunk_length)
                    temp_file.write(chunk)
                    new_resume_size += chunk_length
                    _nb_retries = 5
        except (requests.ConnectionError, requests.ReadTimeout, requests.exceptions.ChunkedEncodingError) as e:
            if _nb_retries <= 0:
                logger.warning("Error while downloading from %s: %s\nMax retries exceeded.", url, str(e))
                raise
            logger.warning("Error while downloading from %s: %s\nTrying to resume download...", url, str(e))
            time.sleep(1)
            reset_sessions()
            return http_get(
                url=url,
                temp_file=temp_file,
                proxies=proxies,
                headers=initial_headers,
                displayed_filename=displayed_filename,
                resume_size=new_resume_size,
                expected_size=expected_size,
                _nb_retries=_nb_retries - 1,
            )

    if expected_size and expected_size != temp_file.tell():
        raise EnvironmentError("File size check failed. Please retry with `force_download=True`")


def _chmod_and_replace(src: str, dst: str) -> None:
    try:
        logger.info(f"chmod {src} 0o640")
        os.chmod(src, mode=0o640)
    except PermissionError:
        logger.warning(f"No permission to chmod: {dst}, please pay attention to file security.")

    logger.info(replace_invalid_characters(f"move {os.path.abspath(src)} to {os.path.abspath(dst)}"))
    shutil.move(src, dst)


@validate_om_hub_args
def try_to_load_from_cache(
    repo_id: str,
    filename: str,
    cache_dir: Union[str, Path, None] = None,
    revision: Optional[str] = None,
    repo_type: Optional[str] = None,
) -> Union[str, _CACHED_NO_EXIST_T, None]:
    """
    Explores the cache to return the latest cached file for a given revision if found.

    This function will not raise any exception if the file in not cached.

    Args:
        cache_dir (`str` or `os.PathLike`):
            The folder where the cached files lie.
        repo_id (`str`):
            The ID of the repo.
        filename (`str`):
            The filename to look for inside `repo_id`.
        revision (`str`, *optional*):
            The specific model version to use. Will default to
            `"main"` if it's not provided and no `commit_hash` is
            provided either.
        repo_type (`str`, *optional*):
            The type of the repository. Will default to `"model"`.

    Returns:
        `Optional[str]` or `_CACHED_NO_EXIST`:
            Will return `None` if the file was not cached. Otherwise:
            - The exact path to the cached file if it's found in the cache
            - A special value `_CACHED_NO_EXIST`
            if the file does not exist at the given commit hash and this fact was
              cached.

    Example:

    ```python
    from openmind_hub import try_to_load_from_cache, _CACHED_NO_EXIST

    filepath = try_to_load_from_cache()
    if isinstance(filepath, str):
        # file exists and is cached
        ...
    elif filepath is _CACHED_NO_EXIST:
        # non-existence of file is cached
        ...
    else:
        # file is not cached
        ...
    ```
    """
    revision = revision or DEFAULT_REVISION
    repo_type = repo_type or REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        error_msg = f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}"
        raise ValueError(replace_invalid_characters(error_msg))
    cache_dir = cache_dir or OM_HUB_CACHE

    # Normalize and validate the cache directory path
    cache_dir = os.path.realpath(cache_dir)
    is_sensitive_path(cache_dir)

    object_id = repo_id.replace("/", "--")
    repo_cache = os.path.join(cache_dir, f"{repo_type}s--{object_id}")
    if not os.path.isdir(repo_cache):
        # No cache for this model
        return None

    refs_dir = os.path.join(repo_cache, "refs")
    snapshots_dir = os.path.join(repo_cache, "snapshots")
    no_exist_dir = os.path.join(repo_cache, ".no_exist")

    # Resolve refs (for instance to convert main to the associated commit sha)
    if os.path.isdir(refs_dir):
        revision_file = os.path.join(refs_dir, revision)
        if os.path.isfile(revision_file) and os.path.getsize(revision_file) < 1024 * 1024:
            with open(revision_file) as f:
                revision = f.read()

    # Check if file is cached as "no_exist"
    if os.path.isfile(os.path.join(no_exist_dir, revision, filename)):
        return _CACHED_NO_EXIST

    # Check if revision folder exists
    if not os.path.exists(snapshots_dir):
        return None
    cached_shas = os.listdir(snapshots_dir)
    if revision not in cached_shas:
        # No cache for this revision and we won't try to return a random revision
        return None

    # Check if file exists in cache
    cached_file = os.path.join(snapshots_dir, revision, filename)
    if os.path.isfile(cached_file):
        check_file_mode(cached_file)
    return cached_file if os.path.isfile(cached_file) else None


def _check_disk_space(expected_size: int, target_dir: Union[str, Path]) -> None:
    """Check disk usage and log a warning if there is not enough disk space to download the file.

    Args:
        expected_size (`int`):
            The expected size of the file in bytes.
        target_dir (`str`):
            The directory where the file will be stored after downloading.
    """

    target_dir = Path(target_dir)  # format as `Path`
    for path in [target_dir] + list(target_dir.parents):  # first check target_dir, then each parents one by one
        try:
            target_dir_free = shutil.disk_usage(path).free
            if target_dir_free < expected_size:
                logger.warning(
                    "Not enough free disk space to download the file. "
                    f"The expected file size is: {expected_size / 1e6:.2f} MB. "
                    f"The target location {target_dir} only has {target_dir_free / 1e6:.2f} MB free disk space."
                )
            return
        except OSError:  # raise on anything: file does not exist or space disk cannot be checked
            logger.warning("file does not exist or space disk cannot be checked")


def _verify_integrity(file_hash: str, file_path: str):
    """
    Verify the integrity of a file by comparing its hash with a provided hash (git-sha1 or sha256).

    Args:
        file_hash (`str`):
            The GIT-SHA-1 or SHA-256 hash to compare against. Must be 40 (SHA-1) or 64 (SHA-256) characters long.
        file_path (`str`):
            The path to the file whose integrity is to be verified.

    """

    def check_sha1(path: str) -> bool:
        if not os.path.exists(path) or os.path.getsize(path) > 100 * ONE_MEGABYTE:
            error_msg = f"""{path} is a regular file and its size must be less than 100MB.
            Please retry with `force_download=True`"""
            raise OMValidationError(replace_invalid_characters(error_msg))
        hash_func = sha1()
        with open(path, "rb") as f:
            file_content = f.read()
        size = len(file_content)
        header = f"blob {size}\0".encode("utf-8")
        hash_func.update(header + file_content)
        return hash_func.hexdigest() == file_hash

    def check_sha256(path: str) -> bool:
        hasher = sha256()
        with open(path, "rb") as f:
            chunk = f.read(8 * ONE_MEGABYTE)
            while chunk:
                hasher.update(chunk)
                chunk = f.read(8 * ONE_MEGABYTE)
        return hasher.hexdigest() == file_hash

    logger.info("checking file hash to verify integrity")
    if len(file_hash) == 40:
        return check_sha1(file_path)
    elif len(file_hash) == 64:
        return check_sha256(file_path)
    else:
        raise OMValidationError("verify integrity failed, invalid file hash. Please retry with `force_download=True`")


@validate_om_hub_args
def om_hub_download(
    repo_id: str,
    filename: str,
    *,
    subfolder: Optional[str] = None,
    repo_type: Optional[str] = None,
    revision: Optional[str] = None,
    cache_dir: Union[str, Path, None] = None,
    local_dir: Union[str, Path, None] = None,
    token: Optional[str] = None,
    force_download: bool = False,
    resume_download: bool = True,
    local_dir_use_symlinks: Union[bool, Literal["auto"]] = "auto",
    local_files_only: bool = False,
    user_agent: Union[Dict, str, None] = None,
    proxies: Optional[Dict] = None,
    endpoint: Optional[str] = None,
    **kwargs,
) -> str:
    """
    args:
    repo_id (`str`):
        A user or an organization name and a repo name separated by a `/`.
    filename (`str`):
        The name of the file in the repo.
    subfolder (`str`, *optional*):
        An optional value corresponding to a folder inside the model repo.
    repo_type (`str`, *optional*):
        Set to `"dataset"` or `"space"` if downloading from a dataset or space,
        `None` or `"model"` if downloading from a model. Default is `None`.
    revision (`str`, *optional*):
        An optional Git branch name
    cache_dir (`str`, `Path`, *optional*):
        Path to the folder where cached files are stored.
    local_dir (`str` or `Path`, *optional*):
        If provided, the downloaded file will be placed under this directory, either as a symlink (default) or
        a regular file (see description for more details).
    local_dir_use_symlinks (`"auto"` or `bool`, defaults to `"auto"`):
        To be used with `local_dir`. If set to "auto", the cache directory will be used and the file will be either
        duplicated or symlinked to the local directory depending on its size. It set to `True`, a symlink will be
        created, no matter the file size. If set to `False`, the file will either be duplicated from cache (if
        already exists) or downloaded from the Hub and not cached.
    user_agent (`dict`, `str`, *optional*):
        The user-agent info in the form of a dictionary or a string.
    force_download (`bool`, *optional*, defaults to `False`):
        Whether the file should be downloaded even if it already exists in
        the local cache.
    proxies (`dict`, *optional*):
        Dictionary mapping protocol to the URL of the proxy passed to
        `requests.request`.
    token (str, bool, *optional*):
        openMind token
    resume_download (`bool`, *optional*, defaults to `True`):
        If `True`, resume a previously interrupted download.
    local_files_only (`bool`, *optional*, defaults to `False`):
        If `True`, avoid downloading the file and return the path to the
        local cached file if it exists.
    Returns:
        Local path (string) of file or if networking is off, last version of
        file cached on disk.
    """
    check_admin()
    revision = revision or DEFAULT_REVISION
    repo_type = repo_type or REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        error_msg = f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}"
        raise ValueError(replace_invalid_characters(error_msg))
    check_repo_exists(repo_id, repo_type, token, endpoint)
    cache_dir = cache_dir or OM_HUB_CACHE
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)
    if isinstance(local_dir, Path):
        local_dir = str(local_dir)
    locks_dir = os.path.join(cache_dir, ".locks")

    if subfolder:
        filename = f"{subfolder}/{filename}"

    if cache_dir:
        is_sensitive_path(cache_dir)
    if local_dir:
        is_sensitive_path(local_dir)

    storage_folder = os.path.join(cache_dir, repo_folder_name(repo_id=repo_id, repo_type=repo_type))
    os.makedirs(storage_folder, mode=0o750, exist_ok=True)

    # Crossing platform transcription of filename, to be used as a local file path.
    relative_filename = str(os.path.join(*filename.split("/")))
    if os.name == "nt":
        if relative_filename.startswith("..\\") or "\\..\\" in relative_filename:
            error_msg = (
                f"Invalid filename: cannot handle filename '{relative_filename}' on Windows. Please ask the repository"
                " owner to rename this file."
            )
            raise ValueError(replace_invalid_characters(error_msg))

    etag = None
    commit_hash = None
    expected_size = None
    head_call_error: Optional[Exception] = None
    metadata = None

    # if user provides a commit_hash, and they already have the file on disk,
    # shortcut everything.
    if REGEX_COMMIT_HASH.match(revision):
        commit_hash = revision
        pointer_path = _get_pointer_path(storage_folder, revision, relative_filename)
        if os.path.exists(pointer_path) and not force_download:
            check_file_mode(pointer_path)
            if local_dir is not None:
                return _to_local_dir(pointer_path, local_dir, relative_filename, use_symlinks=local_dir_use_symlinks)
            return pointer_path

    headers = build_om_headers(user_agent=user_agent, token=token)

    url_to_download = ""

    if not local_files_only:
        try:
            try:
                # Construct the file URL for visiting the openMind hub
                url_to_download = om_hub_url(
                    repo_id,
                    filename,
                    revision=revision,
                    endpoint=endpoint,
                    repo_type=repo_type,
                )

                # Get file metadata for etag and commit_hash, and file size
                params = {"ref": revision, "path": filename}
                endpoint = endpoint or ENDPOINT
                file_metadata_url = f"{endpoint}/api/v1/file/{repo_id}/info?{urlencode(params)}"
                metadata = get_om_file_metadata(
                    url=file_metadata_url,
                    token=token,
                    proxies=proxies,
                    timeout=DEFAULT_REQUEST_TIMEOUT,
                )

                del token
                gc.collect()

            except (OmHubHTTPError, EntryNotFoundError) as e:
                no_exist_file_path = Path(storage_folder) / ".no_exist" / "not_exist_file" / relative_filename
                no_exist_file_path.parent.mkdir(parents=True, mode=0o750, exist_ok=True)
                no_exist_file_path.touch()
                _cache_commit_hash_for_specific_revision(storage_folder, revision, "not_exist_file")
                error_msg = (
                    f"file {filename} not found on {repo_id},"
                    f" or because it is set to `private` and you do not"
                    f" have access."
                )
                raise EntryNotFoundError(replace_invalid_characters(error_msg)) from e

            # Commit hash must exist
            commit_hash = commit_hash or metadata.commit_hash
            if commit_hash is None:
                raise FileMetadataError(
                    "Distant resource does not seem to be on openMind hub. Please check your firewall"
                    " and proxy settings and make sure your SSL certificates are updated."
                )

            # Etag must exist
            etag = metadata.etag
            # We favor a custom header indicating the etag of the linked resource, and
            # we fall back to the regular etag header.
            # If we don't have any of those, raise an error.
            if etag is None:
                raise FileMetadataError(
                    "Distant resource does not have an ETag, we won't be able to reliably ensure reproducibility."
                )

            # Expected (uncompressed) size
            expected_size = metadata.size

        except (requests.exceptions.SSLError, requests.exceptions.ProxyError):
            # Actually raise for those subclasses of ConnectionError
            raise
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:
            # Otherwise, our Internet connection is down.
            # etag is None
            head_call_error = error
        except (RevisionNotFoundError, EntryNotFoundError):
            # The repo was found but the revision or entry doesn't exist on the Hub (never existed or got deleted)
            raise
        except requests.HTTPError as error:
            # Multiple reasons for a http error:
            # - Repository is private and invalid/missing token sent
            # - Repository is gated and invalid/missing token sent
            # - Hub is down (error 500 or 504)
            # => let's switch to 'local_files_only=True' to check if the files are already cached.
            #    (if it's not the case, the error will be re-raised)
            head_call_error = error
        except FileMetadataError as error:
            # Multiple reasons for a FileMetadataError:
            # - Wrong network configuration (proxy, firewall, SSL certificates)
            # - Inconsistency on the Hub
            # => let's switch to 'local_files_only=True' to check if the files are already cached.
            #    (if it's not the case, the error will be re-raised)
            head_call_error = error

    # etag can be None for several reasons:
    # 1. we passed local_files_only.
    # 2. we don't have a connection
    # 3. Hub is down (HTTP 500 or 504)
    # 4. repo is not found -for example private or gated- and invalid/missing token sent
    # 5. Hub is blocked by a firewall or proxy is not set correctly.
    # => Try to get the last downloaded one from the specified revision.
    #
    # If the specified revision is a commit hash, look inside "snapshots".
    # If the specified revision is a branch or tag, look inside "refs".
    if not etag:
        # In those cases, we cannot force download.
        if force_download:
            raise ValueError(
                "We have no connection or you passed local_files_only, so force_download is not an accepted option."
            )

        # Try to get "commit_hash" from "revision"
        commit_hash = None
        if REGEX_COMMIT_HASH.match(revision):
            commit_hash = revision
        else:
            ref_path = os.path.join(storage_folder, "refs", revision)
            if os.path.isfile(ref_path) and os.path.getsize(ref_path) < ONE_MEGABYTE:
                with open(ref_path) as f:
                    commit_hash = f.read()
                    validate_revision(commit_hash)

        # Return pointer file if exists
        if commit_hash is not None:
            pointer_path = _get_pointer_path(storage_folder, commit_hash, relative_filename)
            if os.path.exists(pointer_path):
                check_file_mode(pointer_path)
                if local_dir is not None:
                    return _to_local_dir(
                        pointer_path, local_dir, relative_filename, use_symlinks=local_dir_use_symlinks
                    )
                return pointer_path

        # If we couldn't find an appropriate file on disk, raise an error.
        # If files cannot be found and local_files_only=True,
        # the models might've been found if local_files_only=False
        # Notify the user about that
        if local_files_only:
            raise LocalEntryNotFoundError(
                "Cannot find the requested files in the disk cache and outgoing traffic has been disabled. To enable"
                " downloads online, set 'local_files_only' to False."
            )
        elif isinstance(head_call_error, RepositoryNotFoundError) or isinstance(head_call_error, GatedRepoError):
            # Repo not found => let's raise the actual error
            raise head_call_error
        else:
            # Otherwise: most likely a connection issue or Hub downtime => let's warn the user
            raise LocalEntryNotFoundError(
                "An error happened while trying to locate the file on the Hub and we cannot find the requested files"
                " in the local cache. Please check your connection and try again or make sure your Internet connection"
                " is on."
            ) from head_call_error

    # From now on, etag and commit_hash are not None.
    if not etag:
        raise ValueError("etag must have been retrieved from server.")
    if not commit_hash:
        raise ValueError("commit_hash must have been retrieved from server.")
    blob_path = os.path.join(storage_folder, "blobs", etag)
    pointer_path = _get_pointer_path(storage_folder, commit_hash, relative_filename)

    os.makedirs(os.path.dirname(blob_path), mode=0o750, exist_ok=True)
    os.makedirs(os.path.dirname(pointer_path), mode=0o750, exist_ok=True)
    # if passed revision is not identical to commit_hash
    # then revision has to be a branch name or tag name.
    # In that case store a ref.
    _cache_commit_hash_for_specific_revision(storage_folder, revision, commit_hash)

    if os.path.exists(pointer_path) and not force_download:
        check_file_mode(pointer_path)
        if local_dir is not None:
            return _to_local_dir(pointer_path, local_dir, relative_filename, use_symlinks=local_dir_use_symlinks)
        return pointer_path

    if os.path.exists(blob_path) and not force_download:
        check_file_mode(blob_path)
        # we have the blob already, but not the pointer
        if local_dir:  # to local dir
            return _to_local_dir(blob_path, local_dir, relative_filename, use_symlinks=local_dir_use_symlinks)
        else:  # or in snapshot cache
            _create_symlink(blob_path, pointer_path, new_blob=False)
            return pointer_path

    # Prevent parallel downloads of the same file with a lock.
    # etag could be duplicated across repos,
    lock_path = os.path.join(locks_dir, repo_folder_name(repo_id=repo_id, repo_type=repo_type), f"{etag}.lock")

    # Some Windows versions do not allow for paths longer than 255 characters.
    # In this case, we must specify it is an extended path by using the "\\?\" prefix.
    if os.name == "nt" and len(os.path.abspath(lock_path)) > 255:
        lock_path = "\\\\?\\" + os.path.abspath(lock_path)

    if os.name == "nt" and len(os.path.abspath(blob_path)) > 255:
        blob_path = "\\\\?\\" + os.path.abspath(blob_path)

    Path(lock_path).parent.mkdir(parents=True, mode=0o750, exist_ok=True)
    with FileLock(lock_path):
        # If the download just completed while the lock was activated.
        if os.path.exists(pointer_path) and not force_download:
            check_file_mode(pointer_path)
            # Even if returning early like here, the lock will be released.
            if local_dir is not None:
                return _to_local_dir(pointer_path, local_dir, relative_filename, use_symlinks=local_dir_use_symlinks)
            return pointer_path

        if resume_download:
            incomplete_path = blob_path + ".incomplete"
            file_name = incomplete_path

            @contextmanager
            def _resumable_file_manager() -> Generator[io.BufferedWriter, None, None]:
                import stat

                flags = os.O_WRONLY | os.O_CREAT
                modes = stat.S_IWUSR | stat.S_IRUSR
                with os.fdopen(os.open(incomplete_path, flags, modes), "ab") as f:
                    yield f

            temp_file_manager = _resumable_file_manager
            if os.path.exists(incomplete_path):
                resume_size = os.stat(incomplete_path).st_size
            else:
                resume_size = 0
        else:
            temp_file_manager = partial(tempfile.NamedTemporaryFile, mode="wb", dir=cache_dir, delete=False)
            file_name = ""
            resume_size = 0
            logger.warning("`resume_download` is deprecated and will be removed in later version")

        # Download to temporary file, then copy to cache dir once finished.
        # Otherwise, you get corrupt cache entries if the download gets interrupted.
        with temp_file_manager() as temp_file:
            if not file_name:
                file_name = temp_file.name
            if expected_size is not None:  # might be None if HTTP header not set correctly
                # Check tmp path
                _check_disk_space(expected_size, os.path.dirname(file_name))

                # Check destination
                _check_disk_space(expected_size, os.path.dirname(blob_path))
                if local_dir and not local_dir_use_symlinks:
                    _check_disk_space(expected_size, local_dir)
            # enable dragonfly acceleration
            if "HUB_HTTPS_PROXY" in os.environ:
                proxies = {
                    "https": os.environ["HUB_HTTPS_PROXY"],
                }
            http_get(
                url_to_download,
                temp_file,
                headers=headers,
                proxies=proxies,
                resume_size=resume_size,
                expected_size=expected_size,
            )

        if not local_dir:
            _chmod_and_replace(file_name, blob_path)
            _create_symlink(blob_path, pointer_path, new_blob=True)
        else:
            local_dir_filepath = os.path.join(local_dir, relative_filename)
            os.makedirs(os.path.dirname(local_dir_filepath), mode=0o750, exist_ok=True)

            # If "auto" (default) copy-paste small files to ease manual editing but symlink big files to save disk
            # In both cases, blob file is cached.
            is_big_file = os.stat(file_name).st_size > BIG_FILE_SIZE
            if local_dir_use_symlinks is True or (local_dir_use_symlinks == "auto" and is_big_file):
                _chmod_and_replace(file_name, blob_path)
                _create_symlink(blob_path, local_dir_filepath, new_blob=False)
            elif local_dir_use_symlinks == "auto" and not is_big_file:
                _chmod_and_replace(file_name, blob_path)
                shutil.copyfile(blob_path, local_dir_filepath)
                logger.info(f"chmod {local_dir_filepath} 0o640")
                os.chmod(local_dir_filepath, mode=0o640)
            else:
                _chmod_and_replace(file_name, local_dir_filepath)
            pointer_path = local_dir_filepath  # for return value

    if not local_files_only:
        if not _verify_integrity(metadata.etag, pointer_path):
            error_msg = f"The file {filename} is not downloaded correctly. Please retry with `force_download=True`"
            raise ValueError(replace_invalid_characters(error_msg))
    return pointer_path
