# Copyright (c) Huawei Technologies Co., Ltd. 2023-2023, All rights reserved.
# Copyright 2020 The HuggingFace Team. All rights reserved.
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
import os
import time
import random
from pathlib import Path
from typing import Dict, List, Literal, Optional, TypeVar, Union

from tqdm.auto import tqdm as base_tqdm
from tqdm.contrib.concurrent import thread_map

from .constants import (
    DEFAULT_REVISION,
    OM_HUB_CACHE,
    REGEX_COMMIT_HASH,
    REPO_TYPES,
    REPO_TYPE_MODEL,
    ONE_MEGABYTE,
)
from .file_download import om_hub_download, repo_folder_name, check_repo_exists
from .om_api import OmApi
from .utils._error import LocalEntryNotFoundError
from .utils._path import filter_repo_objects
from .utils._validators import validate_om_hub_args, validate_revision
from .utils.logging import replace_invalid_characters
from .utils.tqdm_hub import Tqdm as om_tqdm


T = TypeVar("T")

IGNORE_GIT_FOLDER_PATTERNS = [".git", ".git/*", "*/.git", "**/.git/**"]


@validate_om_hub_args
def snapshot_download(
    repo_id: str,
    *,
    repo_type: Optional[str] = None,
    revision: Optional[str] = None,
    cache_dir: Union[str, Path, None] = None,
    local_dir: Union[str, Path, None] = None,
    local_dir_use_symlinks: Union[bool, Literal["auto"]] = "auto",
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Optional[Union[Dict, str]] = None,
    proxies: Optional[Dict] = None,
    resume_download: bool = True,
    force_download: bool = False,
    token: Optional[str] = None,
    local_files_only: bool = False,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
    max_workers: int = 8,
    tqdm_class: Optional[base_tqdm] = None,
    endpoint: Optional[str] = None,
    **kwargs,
) -> str:
    """Download repo files.

    Download a whole snapshot of a repo's files at the specified revision. This is useful when you want all files from
    a repo, because you don't know which ones you will need a priori. All files are nested inside a folder in order
    to keep their actual filename relative to that folder. You can also filter which files to download using
    `allow_patterns` and `ignore_patterns`.

    If `local_dir` is provided, the file structure from the repo will be replicated in this location. You can configure
    how you want to move those files:
      - If `local_dir_use_symlinks="auto"` (default), files are downloaded and stored in the cache directory as blob
        files. Small files (<5MB) are duplicated in `local_dir` while a symlink is created for bigger files. The goal
        is to be able to manually edit and save small files without corrupting the cache while saving disk space for
        binary files.
      - If `local_dir_use_symlinks=True`, files are downloaded, stored in the cache directory and symlinked in
        `local_dir`. This is optimal in terms of disk usage but files must not be manually edited.
      - If `local_dir_use_symlinks=False` and the blob files exist in the cache directory, they are duplicated in the
        local dir. This means disk usage is not optimized.
      - Finally, if `local_dir_use_symlinks=False` and the blob files do not exist in the cache directory, then the
        files are downloaded and directly placed under `local_dir`. This means if you need to download them again later,
        they will be re-downloaded entirely.

    An alternative would be to clone the repo but this requires git and git-lfs to be installed and properly
    configured. It is also not possible to filter which files to download when cloning a repository using git.

    Args:
        repo_id (`str`):
            A user or an organization name and a repo name separated by a `/`.
        repo_type (`str`, *optional*):
            Set to `"dataset"` or `"space"` if downloading from a dataset or space,
            `None` or `"model"` if downloading from a model. Default is `None`.
        revision (`str`, *optional*):
            An optional Git revision id which can be a branch name, a tag, or a
            commit hash.
        cache_dir (`str`, `Path`, *optional*):
            Path to the folder where cached files are stored.
        local_dir (`str` or `Path`, *optional*):
            If provided, the downloaded files will be placed under this directory, either as symlinks (default) or
            regular files (see description for more details).
        local_dir_use_symlinks (`"auto"` or `bool`, defaults to `"auto"`):
            To be used with `local_dir`. If set to "auto", the cache directory will be used and the file will be either
            duplicated or symlinked to the local directory depending on its size. It set to `True`, a symlink will be
            created, no matter the file size. If set to `False`, the file will either be duplicated from cache (if
            already exists) or downloaded from the Hub and not cached. See description for more details.
        library_name (`str`, *optional*):
            The name of the library to which the object corresponds.
        library_version (`str`, *optional*):
            The version of the library.
        user_agent (`str`, `dict`, *optional*):
            The user-agent info in the form of a dictionary or a string.
        proxies (`dict`, *optional*):
            Dictionary mapping protocol to the URL of the proxy passed to
            `requests.request`.
        resume_download (`bool`, *optional*, defaults to `True):
            If `True`, resume a previously interrupted download.
        force_download (`bool`, *optional*, defaults to `False`):
            Whether the file should be downloaded even if it already exists in the local cache.
        token (`str`, *optional*):
            A token to be used for the download.
                - If a string, it's used as the authentication token.
        local_files_only (`bool`, *optional*, defaults to `False`):
            If `True`, avoid downloading the file and return the path to the
            local cached file if it exists.
        allow_patterns (`List[str]` or `str`, *optional*):
            If provided, only files matching at least one pattern are downloaded.
        ignore_patterns (`List[str]` or `str`, *optional*):
            If provided, files matching any of the patterns are not downloaded.
        max_workers (`int`, *optional*):
            Number of concurrent threads to download files (1 thread = 1 file download).
            Defaults to 8.
        tqdm_class (`tqdm`, *optional*):
            If provided, overwrites the default behavior for the progress bar. Passed
            argument must inherit from `tqdm.auto.tqdm` or at least mimic its behavior.
            Note that the `tqdm_class` is not passed to each individual download.
            Defaults to the custom OM progress bar that can be disabled by setting
            `OM_HUB_DISABLE_PROGRESS_BARS` environment variable.

    Returns:
        Local folder path (string) of repo snapshot

    <Tip>

    Raises the following errors:

    - [`OSError`](https://docs.python.org/3/library/exceptions.html#OSError) if
      ETag cannot be determined.
    - [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
      if some parameter value is invalid

    </Tip>
    """
    revision = revision or DEFAULT_REVISION
    repo_type = repo_type or REPO_TYPE_MODEL
    if repo_type not in REPO_TYPES:
        error_msg = f"Invalid repo type: {repo_type}. Accepted repo types are: {str(REPO_TYPES)}"
        raise ValueError(replace_invalid_characters(error_msg))
    check_repo_exists(repo_id, repo_type, token, endpoint)
    cache_dir = cache_dir or OM_HUB_CACHE
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    storage_folder = os.path.join(cache_dir, repo_folder_name(repo_id=repo_id, repo_type=repo_type))

    # if we have no internet connection we will look for an
    # appropriate folder in the cache
    # If the specified revision is a commit hash, look inside "snapshots".
    # If the specified revision is a branch or tag, look inside "refs".
    if local_files_only:
        if REGEX_COMMIT_HASH.match(revision):
            commit_hash = revision
        else:
            # retrieve commit_hash from file
            ref_path = os.path.join(storage_folder, "refs", revision)
            if os.path.isfile(ref_path) and os.path.getsize(ref_path) < ONE_MEGABYTE:
                with open(ref_path) as f:
                    commit_hash = f.read()
                    validate_revision(commit_hash)
            else:
                raise LocalEntryNotFoundError(
                    "Cannot find the requested files in the disk cache and outgoing traffic has been disabled."
                    " To enable downloads online, set 'local_files_only' to False."
                )

        snapshot_folder = os.path.join(storage_folder, "snapshots", commit_hash)

        if os.path.exists(snapshot_folder):
            return snapshot_folder

        raise LocalEntryNotFoundError(
            "Cannot find an appropriate cached snapshot folder for the specified"
            " revision on the local disk and outgoing traffic has been disabled. To"
            " enable repo look-ups and downloads online, set 'local_files_only' to"
            " False."
        )

    # if we have internet connection we retrieve the correct folder name from the openmind api
    api = OmApi(
        library_name=library_name,
        library_version=library_version,
        user_agent=user_agent,
        endpoint=endpoint,
        token=token,
    )
    files = api.list_repo_files(repo_id=repo_id, revision=revision, token=token)
    filtered_repo_files = list(
        filter_repo_objects(
            items=[file for file in files],
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )
    )
    commit_hash = api.get_repo_last_commit(repo_id=repo_id, revision=revision, token=token).oid

    ref_path = Path(storage_folder) / "refs" / revision
    ref_path.parent.mkdir(parents=True, mode=0o750, exist_ok=True)
    if not ref_path.exists() or os.path.getsize(ref_path) >= ONE_MEGABYTE or commit_hash != ref_path.read_text():
        ref_path.write_text(commit_hash)

    def _inner_om_hub_download(repo_file: str):
        retry_attempts = 0
        max_retries = 10  # 定义最大重试次数

        while retry_attempts < max_retries:
            try:
                return om_hub_download(
                    repo_id,
                    filename=repo_file,
                    repo_type=repo_type,
                    revision=revision,
                    endpoint=endpoint,
                    cache_dir=cache_dir,
                    local_dir=local_dir,
                    local_dir_use_symlinks=local_dir_use_symlinks,
                    user_agent=user_agent,
                    proxies=proxies,
                    resume_download=resume_download,
                    force_download=force_download,
                    token=token,
                )
            except Exception as e:  # 捕获所有异常
                retry_attempts += 1
                if retry_attempts >= max_retries:
                    raise RuntimeError(f"Download failed after {max_retries} attempts") from e

                backoff_time = min(10, (2**retry_attempts) + random.uniform(0, 1))
                time.sleep(backoff_time)

    thread_map(
        _inner_om_hub_download,
        filtered_repo_files,
        desc=f"Fetching {len(filtered_repo_files)} files",
        max_workers=max_workers,
        # User can use its own tqdm class or the default one from `.utils`
        tqdm_class=tqdm_class or om_tqdm,
    )

    if local_dir:
        return str(os.path.realpath(local_dir))
    snapshot_folder = os.path.join(storage_folder, "snapshots", commit_hash)
    return snapshot_folder
