# Copyright (c) Huawei Technologies Co., Ltd. 2023-2023, All rights reserved.
# Copyright 2019-present, the HuggingFace Inc. team.
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
import re
import tempfile
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union
from urllib.parse import quote, unquote

import fsspec
from fsspec import AbstractFileSystem
from fsspec.callbacks import _DEFAULT_CALLBACK, NoOpCallback, TqdmCallback
from fsspec.utils import isfilelike
from requests import Response

from ._commit_api import CommitOperationDelete
from .constants import (
    DEFAULT_REVISION,
    ENDPOINT,
    DEFAULT_DOWNLOAD_TIMEOUT,
    DEFAULT_ETAG_TIMEOUT,
    REPO_TYPE_MODEL,
    REPO_TYPES_MAPPING,
    REPO_TYPES_URL_PREFIXES,
)
from .file_download import om_hub_url, http_get
from .om_api import OmApi, RepoFile, RepoFolder
from .utils import (
    OmHubHTTPError,
    EntryNotFoundError,
    OMValidationError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
    om_raise_for_status,
)
from .utils._http import http_backoff
from .utils._validators import is_sensitive_path


# Regex used to match special revisions with "/" in them (see #1710)
SPECIAL_REFS_REVISION_REGEX = re.compile(
    r"""
    (^refs/convert/\w+)     # `refs/convert/parquet` revisions
    |
    (^refs/pr/\d+)          # PR revisions
    """,
    re.VERBOSE,
)


@dataclass
class OmFileSystemResolvedPath:
    """Data structure containing information about a resolved openMind file system path."""

    repo_type: str
    repo_id: str
    revision: str
    path_in_repo: str
    # The part placed after '@' in the initial path. It can be a quoted or unquoted refs revision.
    # Used to reconstruct the unresolved path to return to the user.
    raw_revision: Optional[str] = field(default=None, repr=False)

    def unresolve(self) -> str:
        repo_path = REPO_TYPES_URL_PREFIXES.get(self.repo_type, "") + self.repo_id
        if self.raw_revision:
            return f"{repo_path}@{self.raw_revision}/{self.path_in_repo}".rstrip("/")
        elif self.revision != DEFAULT_REVISION:
            return f"{repo_path}@{safe_revision(self.revision)}/{self.path_in_repo}".rstrip("/")
        else:
            return f"{repo_path}/{self.path_in_repo}".rstrip("/")


class OmFileSystem(AbstractFileSystem):
    """
    Access a remote openMind Hub repository as if were a local file system.

    Args:
        token (`str`, *optional*):
            Authentication token.

    Usage:

    ```python
    >>> from openmind_hub import OmFileSystem

    >>> fs = OmFileSystem()

    >>> # List files
    >>> fs.glob("my-username/my-model/*.bin")
    ['my-username/my-model/pytorch_model.bin']
    >>> fs.ls("datasets/my-username/my-dataset", detail=False)
    ['datasets/my-username/my-dataset/.gitattributes', 'datasets/my-username/my-dataset/README.md',
    'datasets/my-username/my-dataset/data.json']

    >>> # Read/write files
    >>> with fs.open("my-username/my-model/pytorch_model.bin") as f:
    ...     data = f.read()
    >>> with fs.open("my-username/my-model/pytorch_model.bin", "wb") as f:
    ...     f.write(data)
    ```
    """

    def __init__(
        self,
        *args,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        **storage_options,
    ):
        super().__init__(*args, **storage_options)
        self.endpoint = endpoint or ENDPOINT
        self.token = token
        self.api = OmApi(endpoint=endpoint, token=token)
        # Maps (repo_type, repo_id, revision) to a 2-tuple with:
        #  * the 1st element indicating whether the repositoy and the revision exist
        #  * the 2nd element being the exception raised if the repository or revision doesn't exist
        self._repo_and_revision_exists_cache: Dict = {}

    @property
    def transaction(self):
        """A context within which files are committed together upon exit

        Requires the file class to implement `.commit()` and `.discard()`
        for the normal and exception cases.
        """
        raise NotImplementedError("Transactional commits are not supported.")

    def resolve_path(self, path: str, revision: Optional[str] = None) -> OmFileSystemResolvedPath:
        def _align_revision_in_path_with_revision(
            revision_in_path: Optional[str], revision: Optional[str]
        ) -> Optional[str]:
            if revision is not None:
                if revision_in_path is not None and revision_in_path != revision:
                    raise ValueError(
                        f'Revision specified in path ("{revision_in_path}") and in `revision` argument ("{revision}")'
                        " are not the same."
                    )
            else:
                revision = revision_in_path
            return revision

        path = self._strip_protocol(path)
        if not path:
            # can't list repositories at root
            raise NotImplementedError("Access to repositories lists is not implemented.")
        elif path.split("/")[0] + "/" in REPO_TYPES_URL_PREFIXES.values():
            if "/" not in path:
                # can't list repositories at the repository type level
                raise NotImplementedError("Access to repositories lists is not implemented.")
            repo_type, path = path.split("/", 1)
            repo_type = REPO_TYPES_MAPPING.get(repo_type)
            if not repo_type:
                raise ValueError("invalid repo_type")
        else:
            repo_type = REPO_TYPE_MODEL
        if path.count("/") > 0:
            if "@" in path:
                repo_id, revision_in_path = path.split("@", 1)
                if "/" in revision_in_path:
                    match = SPECIAL_REFS_REVISION_REGEX.search(revision_in_path)
                    if match is not None and revision in (None, match.group()):
                        # Handle `refs/convert/parquet` and PR revisions separately
                        path_in_repo = SPECIAL_REFS_REVISION_REGEX.sub("", revision_in_path).lstrip("/")
                        revision_in_path = match.group()
                    else:
                        revision_in_path, path_in_repo = revision_in_path.split("/", 1)
                else:
                    path_in_repo = ""
                revision = _align_revision_in_path_with_revision(unquote(revision_in_path), revision)
                repo_and_revision_exist, err = self._repo_and_revision_exist(repo_type, repo_id, revision)
                if not repo_and_revision_exist:
                    _raise_file_not_found(path, err)
            else:
                revision_in_path = None
                repo_id = "/".join(path.split("/")[:2])
                path_in_repo = "/".join(path.split("/")[2:])
                repo_and_revision_exist, err = self._repo_and_revision_exist(repo_type, repo_id, revision)
                if not repo_and_revision_exist:
                    _raise_file_not_found(path, err)
        else:
            raise ValueError("invalid repo_id in path")

        revision = revision if revision is not None else DEFAULT_REVISION
        return OmFileSystemResolvedPath(repo_type, repo_id, revision, path_in_repo, raw_revision=revision_in_path)

    def invalidate_cache(self, path: Optional[str] = None) -> None:
        if not path:
            self.dircache.clear()
            self._repo_and_revision_exists_cache.clear()
        else:
            path = self.resolve_path(path).unresolve()
            while path:
                self.dircache.pop(path, None)
                path = self._parent(path)

    def rm(
        self,
        path: str,
        recursive: bool = False,
        maxdepth: Optional[int] = None,
        revision: Optional[str] = None,
        **kwargs,
    ) -> None:
        resolved_path = self.resolve_path(path, revision=revision)
        paths = self.expand_path(path, recursive=recursive, maxdepth=maxdepth, revision=revision)
        paths_in_repo = [self.resolve_path(path).path_in_repo for path in paths if not self.isdir(path)]
        operations = [CommitOperationDelete(path_in_repo=path_in_repo) for path_in_repo in paths_in_repo]
        commit_message = f"Delete {path} "
        commit_message += "recursively " if recursive else ""
        commit_message += f"up to depth {maxdepth} " if maxdepth is not None else ""
        self.api.create_commit(
            repo_id=resolved_path.repo_id,
            token=self.token,
            operations=operations,
            revision=resolved_path.revision,
            commit_message=kwargs.get("commit_message", commit_message),
            commit_description=kwargs.get("commit_description"),
        )
        self.invalidate_cache(path=resolved_path.unresolve())

    def ls(
        self, path: str, detail: bool = True, refresh: bool = False, revision: Optional[str] = None, **kwargs
    ) -> List[Union[str, Dict[str, Any]]]:
        """列出目录下所有文件和目录名称或详细信息，返回列表"""
        resolved_path = self.resolve_path(path, revision=revision)
        path = resolved_path.unresolve()
        kwargs = {"expand_info": detail, **kwargs}
        try:
            repo_tree = self._ls_tree(path, refresh=refresh, revision=revision, **kwargs)
        except EntryNotFoundError:
            # Path could be a file
            if not resolved_path.path_in_repo:
                _raise_file_not_found(path, None)
            repo_tree = self._ls_tree(self._parent(path), refresh=refresh, revision=revision, **kwargs)
            repo_tree = [path_info for path_info in repo_tree if path_info["name"] == path]
            if len(repo_tree) == 0:
                _raise_file_not_found(path, None)
        return repo_tree if detail else [path_info.get("name") for path_info in repo_tree]

    def glob(self, path, **kwargs):
        """使用格式匹配过滤`path`下的文件，非递归"""
        # Set expand_info=False by default to get a x10 speed boost
        kwargs = {"expand_info": kwargs.get("detail", False), **kwargs}
        path = self.resolve_path(path, revision=kwargs.get("revision")).unresolve()
        return super().glob(path, **kwargs)

    def find(
        self,
        path: str,
        maxdepth: Optional[int] = None,
        detail: Optional[bool] = False,
        withdirs: bool = False,
        refresh: bool = False,
        revision: Optional[str] = None,
        **kwargs,
    ) -> Union[List[str], Dict[str, Dict[str, Any]]]:
        """递归查找`path`下的所有文件及文件信息，不包含目录。返回字典"""
        if maxdepth:
            return super().find(
                path, maxdepth=maxdepth, withdirs=withdirs, detail=detail, refresh=refresh, revision=revision, **kwargs
            )
        resolved_path = self.resolve_path(path, revision=revision)
        path = resolved_path.unresolve()
        kwargs = {"expand_info": detail, **kwargs}
        try:
            repo_tree = self._ls_tree(path, recursive=True, refresh=refresh, revision=resolved_path.revision, **kwargs)
        except EntryNotFoundError:
            # Path could be a file
            if self.info(path, revision=revision, **kwargs).get("type") == "file":
                repo_tree_dir = {path: {}}
            else:
                repo_tree_dir = {}
        else:
            if not withdirs:
                repo_tree = [file for file in repo_tree if file.get("type") != "directory"]
            else:
                # If `withdirs=True`, include the directory itself to be consistent with the spec
                path_info = self.info(path, revision=resolved_path.revision, **kwargs)
                repo_tree = [path_info] + repo_tree if path_info.get("type") == "directory" else repo_tree
            repo_tree_dir = {file.get("name"): file for file in repo_tree}
        names = sorted(repo_tree_dir)
        if not detail:
            return names
        return {name: repo_tree_dir.get(name) for name in names}

    def modified(self, path: str, **kwargs) -> datetime:
        info = self.info(path, **kwargs)
        return info.get("last_commit").get("date")

    def info(self, path: str, refresh: bool = False, revision: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        resolved_path = self.resolve_path(path, revision=revision)
        path = resolved_path.unresolve()
        if not resolved_path.path_in_repo:
            # Path is the root directory
            last_commit = self.api.get_repo_last_commit(resolved_path.repo_id, revision=resolved_path.revision)
            path_info = {
                "name": path,
                "size": 0,
                "type": "directory",
                "last_commit": last_commit,
            }
        else:
            path_info = None
            parent_path = self._parent(path)
            if parent_path in self.dircache:
                # Check if the path is in the cache
                infos = [info for info in self.dircache[parent_path] if info.get("name") == path]
                if not infos:
                    _raise_file_not_found(path, None)
                path_info = infos[0]
            out_bool = path_info and path_info.get("last_commit") is None
            root_path = OmFileSystemResolvedPath(
                resolved_path.repo_type,
                resolved_path.repo_id,
                resolved_path.revision,
                path_in_repo="",
                raw_revision=resolved_path.raw_revision,
            ).unresolve()
            if refresh or path_info is None or out_bool:
                try:
                    path_info = self.api.get_path_info(
                        resolved_path.repo_id,
                        revision=resolved_path.revision,
                        path_in_repo=resolved_path.path_in_repo,
                    )
                except Exception as e:
                    _raise_file_not_found(resolved_path.path_in_repo, e)

                if isinstance(path_info, RepoFile):
                    path_info = {
                        "name": root_path + "/" + path_info.path,
                        "size": path_info.size,
                        "type": "file",
                        "blob_id": path_info.blob_id,
                        "lfs": path_info.lfs,
                        "last_commit": path_info.last_commit,
                    }
                elif isinstance(path_info, RepoFolder):
                    path_info = {
                        "name": root_path + "/" + path_info.path,
                        "size": 0,
                        "type": "directory",
                        "last_commit": path_info.last_commit,
                    }
        if path_info is None:
            raise ValueError("get no path info")
        return path_info

    def exists(self, path, **kwargs) -> bool:
        """Is there a file at the given path"""
        try:
            self.info(path, **kwargs)
            return True
        except (OmHubHTTPError, OSError):
            # any exception allowed bar FileNotFoundError?
            return False

    def isdir(self, path) -> bool:
        """Is this entry directory-like?"""
        try:
            return self.info(path).get("type") == "directory"
        except (OmHubHTTPError, OSError):
            return False

    def isfile(self, path) -> bool:
        """Is this entry file-like?"""
        try:
            return self.info(path).get("type") == "file"
        except (OmHubHTTPError, OSError):
            return False

    def url(self, path: str) -> str:
        """Get the HTTP URL of the given path"""
        resolved_path = self.resolve_path(path)
        url = om_hub_url(
            resolved_path.repo_id,
            resolved_path.path_in_repo,
            repo_type=resolved_path.repo_type,
            revision=resolved_path.revision,
            endpoint=self.endpoint,
        )
        return url

    def get_file(self, rpath, lpath, callback=_DEFAULT_CALLBACK, outfile=None, **kwargs) -> None:
        """Copy single remote file to local."""
        is_sensitive_path(lpath)
        revision = kwargs.get("revision")
        unhandled_kwargs = set(kwargs.keys()) - {"revision"}
        if not isinstance(callback, (NoOpCallback, TqdmCallback)) or len(unhandled_kwargs) > 0:
            # for now, let's not handle custom callbacks
            # and let's not handle custom kwargs
            super().get_file(rpath, lpath, callback=callback, outfile=outfile, **kwargs)
            return

        if isfilelike(lpath):
            outfile = lpath
        elif self.isdir(rpath):
            os.makedirs(lpath, exist_ok=True)
            return

        if isinstance(lpath, (str, Path)):  # otherwise, let's assume it's a file-like object
            os.makedirs(os.path.dirname(lpath), exist_ok=True)

        # Open file if not already open
        close_file = False
        import stat

        if outfile is None:
            flags = os.O_WRONLY | os.O_CREAT
            modes = stat.S_IWUSR | stat.S_IRUSR
            outfile = os.fdopen(os.open(lpath, flags, modes), "wb")
            close_file = True
        initial_pos = outfile.tell()

        # Custom implementation of `get_file` to use `http_get`.
        resolve_remote_path = self.resolve_path(rpath, revision=revision)
        expected_size = self.info(rpath, revision=revision).get("size")
        callback.set_size(expected_size)
        try:
            http_get(
                url=om_hub_url(
                    repo_id=resolve_remote_path.repo_id,
                    revision=resolve_remote_path.revision,
                    filename=resolve_remote_path.path_in_repo,
                    repo_type=resolve_remote_path.repo_type,
                    endpoint=self.endpoint,
                ),
                temp_file=outfile,
                displayed_filename=rpath,
                expected_size=expected_size,
                resume_size=0,
                headers=self.api.build_om_headers(),
                _tqdm_bar=callback.tqdm if isinstance(callback, TqdmCallback) else None,
            )
            outfile.seek(initial_pos)
        finally:
            # Close file only if we opened it ourselves
            if close_file:
                outfile.close()

    def start_transaction(self):
        """Begin write transaction for deferring files, non-context version"""
        raise NotImplementedError("Transactional commits are not supported.")

    def _open(
        self,
        path: str,
        mode: str = "rb",
        revision: Optional[str] = None,
        block_size: Optional[int] = None,
        **kwargs,
    ) -> Union["OmFileSystemFile", "OmFileSystemStreamFile"]:
        if "a" in mode:
            raise NotImplementedError("Appending to remote files is not yet supported.")
        if block_size == 0:
            return OmFileSystemStreamFile(self, path, mode=mode, revision=revision, block_size=block_size, **kwargs)
        else:
            return OmFileSystemFile(self, path, mode=mode, revision=revision, block_size=block_size, **kwargs)

    def _repo_and_revision_exist(
        self, repo_type: str, repo_id: str, revision: Optional[str]
    ) -> Tuple[bool, Optional[Exception]]:
        if (repo_type, repo_id, revision) not in self._repo_and_revision_exists_cache:
            try:
                self.api.repo_info(repo_id, revision=revision, repo_type=repo_type, timeout=DEFAULT_ETAG_TIMEOUT)
            except (RepositoryNotFoundError, OMValidationError) as e:
                self._repo_and_revision_exists_cache[(repo_type, repo_id, revision)] = False, e
                self._repo_and_revision_exists_cache[(repo_type, repo_id, None)] = False, e
            except RevisionNotFoundError as e:
                self._repo_and_revision_exists_cache[(repo_type, repo_id, revision)] = False, e
                self._repo_and_revision_exists_cache[(repo_type, repo_id, None)] = True, None
            else:
                self._repo_and_revision_exists_cache[(repo_type, repo_id, revision)] = True, None
                self._repo_and_revision_exists_cache[(repo_type, repo_id, None)] = True, None
        return self._repo_and_revision_exists_cache[(repo_type, repo_id, revision)]

    def _rm(self, path: str, revision: Optional[str] = None, **kwargs) -> None:
        resolved_path = self.resolve_path(path, revision=revision)
        self.api.delete_file(
            path_in_repo=resolved_path.path_in_repo,
            repo_id=resolved_path.repo_id,
            token=self.token,
            repo_type=resolved_path.repo_type,
            revision=resolved_path.revision,
            commit_message=kwargs.get("commit_message"),
            commit_description=kwargs.get("commit_description"),
        )
        self.invalidate_cache(path=resolved_path.unresolve())

    def _ls_tree(
        self,
        path: str,
        recursive: bool = False,
        refresh: bool = False,
        revision: Optional[str] = None,
        expand_info: bool = True,
        **kwargs,
    ):
        resolved_path = self.resolve_path(path, revision=revision)
        path = resolved_path.unresolve()
        root_path = OmFileSystemResolvedPath(
            resolved_path.repo_type,
            resolved_path.repo_id,
            resolved_path.revision,
            path_in_repo="",
            raw_revision=resolved_path.raw_revision,
        ).unresolve()

        repo_tree = []
        if path in self.dircache and not refresh:
            cached_path_infos = self.dircache[path]
            repo_tree.extend(cached_path_infos)
            dirs_not_in_dircache = []
            if recursive:
                # Use BFS to traverse the cache and build the "recursive "output
                dirs_to_visit = deque(
                    [path_info for path_info in cached_path_infos if path_info.get("type") == "directory"]
                )
                while dirs_to_visit:
                    dir_info = dirs_to_visit.popleft()
                    if dir_info.get("name") not in self.dircache:
                        dirs_not_in_dircache.append(dir_info.get("name"))
                    else:
                        cached_path_infos = self.dircache[dir_info.get("name")]
                        repo_tree.extend(cached_path_infos)
                        dirs_to_visit.extend(
                            [path_info for path_info in cached_path_infos if path_info.get("type") == "directory"]
                        )

            dirs_not_expanded = []
            if expand_info:
                # Check if there are directories with non-expanded entries
                dirs_not_expanded = [
                    self._parent(path_info.get("name"))
                    for path_info in repo_tree
                    if path_info.get("last_commit") is None
                ]

            expand_bool = expand_info and dirs_not_expanded
            if (recursive and dirs_not_in_dircache) or expand_bool:
                # If the dircache is incomplete, find the common path of the missing and non-expanded entries
                # and extend the output with the result of `_ls_tree(common_path, recursive=True)`
                common_prefix = os.path.commonprefix(dirs_not_in_dircache + dirs_not_expanded)
                # Get the parent directory if the common prefix itself is not a directory
                common_path = (
                    common_prefix.rstrip("/")
                    if common_prefix.endswith("/")
                    or common_prefix == root_path
                    or common_prefix in chain(dirs_not_in_dircache, dirs_not_expanded)
                    else self._parent(common_prefix)
                )
                repo_tree = [
                    path_info for path_info in repo_tree if not path_info.get("name").startswith(common_path + "/")
                ]
                for cached_path in self.dircache:
                    if cached_path.startswith(common_path + "/"):
                        self.dircache.pop(cached_path, None)
                self.dircache.pop(common_path, None)
                repo_tree.extend(
                    self._ls_tree(
                        common_path,
                        recursive=recursive,
                        refresh=True,
                        revision=revision,
                        expand_info=expand_info,
                    )
                )
        else:
            tree = self.api.list_repo_tree(
                resolved_path.repo_id,
                resolved_path.path_in_repo,
                revision=resolved_path.revision,
                recursive=recursive,
            )
            for path_info in tree:
                if isinstance(path_info, RepoFile):
                    cache_path_info = {
                        "name": root_path + "/" + path_info.path,
                        "size": path_info.size,
                        "type": "file",
                        "blob_id": path_info.blob_id,
                        "lfs": path_info.lfs,
                        "last_commit": path_info.last_commit,
                    }
                else:
                    cache_path_info = {
                        "name": root_path + "/" + path_info.path,
                        "size": 0,
                        "type": "directory",
                        "last_commit": path_info.last_commit,
                    }
                parent_path = self._parent(cache_path_info.get("name"))
                self.dircache.setdefault(parent_path, []).append(cache_path_info)
                repo_tree.append(cache_path_info)
        return repo_tree


class OmFileSystemFile(fsspec.spec.AbstractBufferedFile):
    def __init__(self, fs: OmFileSystem, path: str, revision: Optional[str] = None, **kwargs):
        try:
            self.resolved_path = fs.resolve_path(path, revision=revision)
        except FileNotFoundError as e:
            if "w" in kwargs.get("mode", ""):
                raise FileNotFoundError(
                    f"{e}.\nMake sure the repository and revision exist before writing data."
                ) from e
            raise
        super().__init__(fs, self.resolved_path.unresolve(), **kwargs)
        self.fs: OmFileSystem

    def __del__(self):
        if hasattr(self, "resolved_path"):
            super().__del__()

    def read(self, length=-1):
        """Read remote file."""
        length_bool = length == -1 or length is None
        if self.mode == "rb" and length_bool and self.loc == 0:
            with self.fs.open(self.path, "rb", block_size=0) as f:  # block_size=0 enables fast streaming
                return f.read()
        return super().read(length)

    def url(self) -> str:
        return self.fs.url(self.path)

    def _fetch_range(self, start: int, end: int) -> bytes:
        headers = {
            "range": f"bytes={start}-{end - 1}",
            **self.fs.api.build_om_headers(),
        }
        url = om_hub_url(
            repo_id=self.resolved_path.repo_id,
            revision=self.resolved_path.revision,
            filename=self.resolved_path.path_in_repo,
            repo_type=self.resolved_path.repo_type,
            endpoint=self.fs.endpoint,
        )
        r = http_backoff(
            "GET",
            url,
            headers=headers,
            retry_on_status_codes=(502, 503, 504),
            timeout=DEFAULT_DOWNLOAD_TIMEOUT,
        )
        om_raise_for_status(r)
        return r.content

    def _initiate_upload(self) -> None:
        self.temp_file = tempfile.NamedTemporaryFile(prefix="hffs-", delete=False, dir=os.path.expanduser("~"))

    def _upload_chunk(self, final: bool = False) -> None:
        self.buffer.seek(0)
        block = self.buffer.read()
        self.temp_file.write(block)
        if final:
            self.temp_file.close()
            self.fs.api.upload_file(
                path_or_fileobj=self.temp_file.name,
                path_in_repo=self.resolved_path.path_in_repo,
                repo_id=self.resolved_path.repo_id,
                token=self.fs.token,
                repo_type=self.resolved_path.repo_type,
                revision=self.resolved_path.revision,
                commit_message=self.kwargs.get("commit_message"),
                commit_description=self.kwargs.get("commit_description"),
            )
            os.remove(self.temp_file.name)
            self.fs.invalidate_cache(
                path=self.resolved_path.unresolve(),
            )


class OmFileSystemStreamFile(fsspec.spec.AbstractBufferedFile):
    def __init__(
        self,
        fs: OmFileSystem,
        path: str,
        mode: str = "rb",
        revision: Optional[str] = None,
        block_size: int = 0,
        cache_type: str = "none",
        **kwargs,
    ):
        if block_size != 0:
            raise ValueError(f"OmFileSystemStreamFile only supports block_size=0 but got {block_size}")
        if cache_type != "none":
            raise ValueError(f"OmFileSystemStreamFile only supports cache_type='none' but got {cache_type}")
        if "w" in mode:
            raise ValueError(f"OmFileSystemStreamFile only supports reading but got mode='{mode}'")
        try:
            self.resolved_path = fs.resolve_path(path, revision=revision)
        except FileNotFoundError as e:
            if "w" in kwargs.get("mode", ""):
                raise FileNotFoundError(
                    f"{e}.\nMake sure the repository and revision exist before writing data."
                ) from e
        # avoid an unnecessary .info() call to instantiate .details
        self.details = {"name": self.resolved_path.unresolve(), "size": None}
        super().__init__(
            fs, self.resolved_path.unresolve(), mode=mode, block_size=block_size, cache_type=cache_type, **kwargs
        )
        self.response: Optional[Response] = None
        self.fs: OmFileSystem

    def __del__(self):
        if hasattr(self, "resolved_path"):
            super().__del__()

    def __reduce__(self):
        return reopen, (self.fs, self.path, self.mode, self.blocksize, self.cache.name)

    def seek(self, loc: int, whence: int = 0):
        if loc == 0 and whence == 1:
            return
        if loc == self.loc and whence == 0:
            return
        raise ValueError("Cannot seek streaming OM file")

    def read(self, length: int = -1):
        read_args = (length,) if length >= 0 else ()
        if self.response is None or self.response.raw.isclosed():
            url = om_hub_url(
                repo_id=self.resolved_path.repo_id,
                revision=self.resolved_path.revision,
                filename=self.resolved_path.path_in_repo,
                repo_type=self.resolved_path.repo_type,
                endpoint=self.fs.endpoint,
            )
            self.response = http_backoff(
                "GET",
                url,
                headers=self.fs.api.build_om_headers(),
                retry_on_status_codes=(502, 503, 504),
                stream=True,
                timeout=DEFAULT_DOWNLOAD_TIMEOUT,
            )
            om_raise_for_status(self.response)
        try:
            out = self.response.raw.read(*read_args)
        except Exception:
            self.response.close()

            # Retry by recreating the connection
            url = om_hub_url(
                repo_id=self.resolved_path.repo_id,
                revision=self.resolved_path.revision,
                filename=self.resolved_path.path_in_repo,
                repo_type=self.resolved_path.repo_type,
                endpoint=self.fs.endpoint,
            )
            self.response = http_backoff(
                "GET",
                url,
                headers={"Range": "bytes=%d-" % self.loc, **self.fs.api.build_om_headers()},
                retry_on_status_codes=(502, 503, 504),
                stream=True,
                timeout=DEFAULT_DOWNLOAD_TIMEOUT,
            )
            om_raise_for_status(self.response)
            try:
                out = self.response.raw.read(*read_args)
            except Exception:
                self.response.close()
                raise
        self.loc += len(out)
        return out

    def url(self) -> str:
        return self.fs.url(self.path)


def safe_revision(revision: str) -> str:
    return revision if SPECIAL_REFS_REVISION_REGEX.match(revision) else safe_quote(revision)


def safe_quote(s: str) -> str:
    return quote(s, safe="")


def _raise_file_not_found(path: str, err: Optional[Exception]) -> NoReturn:
    msg = path
    if isinstance(err, RepositoryNotFoundError):
        msg = f"{path} (repository not found)"
    elif isinstance(err, RevisionNotFoundError):
        msg = f"{path} (revision not found)"
    elif isinstance(err, OMValidationError):
        msg = f"{path} (invalid repository id)"
    raise FileNotFoundError(msg) from err


def reopen(fs: OmFileSystem, path: str, mode: str, block_size: int, cache_type: str):
    return fs.open(path, mode=mode, block_size=block_size, cache_type=cache_type)
