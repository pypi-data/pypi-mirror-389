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
import os
from pathlib import Path
from typing import BinaryIO, Dict, Iterable, List, Literal, Optional, Union
from tqdm.auto import tqdm

from openmind_hub.interface.base_api import BaseApi, CommitOperation
from openmind_hub.interface.dependent_methods import _CACHED_NO_EXIST_T, DEFAULT_REQUEST_TIMEOUT
from openmind_hub.plugins import openmind
from openmind_hub.plugins.utils.import_utils import is_openi_available, is_hf_available


def get_plugin(platform: str = None):
    platform = platform or os.getenv("OPENMIND_PLATFORM")
    if platform == "gitee":
        os.environ["HF_ENDPOINT"] = "https://hf-api.gitee.com"
        platform = "huggingface"
    elif platform == "gitcode":
        platform = "openmind"

    if platform is None or platform == "openmind":
        module = openmind
    elif platform == "openi":
        if not is_openi_available():
            raise ImportError("openi was not found in your environment. Please install and restart your runtime.")
        from openmind_hub.plugins import openi

        module = openi
    elif platform == "huggingface":
        if not is_hf_available():
            raise ImportError(
                "huggingface_hub was not found in your environment. Please install and restart your runtime."
            )
        from openmind_hub.plugins import huggingface

        module = huggingface
    else:
        raise ValueError("unknown platform")
    return module


# 常数和类初始化后不会再变化，函数都可以通过设置环境变量或传递`platform`参数决定访问的服务端。
class HubApi(BaseApi):
    OmApi = get_plugin().OmApi
    RepoUrl = get_plugin().RepoUrl
    RepoFile = get_plugin().RepoFile
    RepoFolder = get_plugin().RepoFolder
    ModelInfo = get_plugin().ModelInfo
    ModelFilter = get_plugin().ModelFilter
    DatasetInfo = get_plugin().DatasetInfo
    CommitOperationAdd = get_plugin().CommitOperationAdd
    CommitOperationDelete = get_plugin().CommitOperationDelete
    Repository = get_plugin().Repository
    DatasetCard = get_plugin().DatasetCard
    DatasetCardData = get_plugin().DatasetCardData
    OmFileSystem = get_plugin().OmFileSystem
    OMValidationError = get_plugin().OMValidationError
    EntryNotFoundError = get_plugin().EntryNotFoundError
    RepositoryNotFoundError = get_plugin().RepositoryNotFoundError
    RevisionNotFoundError = get_plugin().RevisionNotFoundError
    GatedRepoError = get_plugin().GatedRepoError
    LocalEntryNotFoundError = get_plugin().LocalEntryNotFoundError
    OmHubHTTPError = get_plugin().OmHubHTTPError

    @property
    def OM_HOME(self):
        module = get_plugin()
        return module.OM_HOME

    @property
    def OM_HUB_CACHE(self):
        module = get_plugin()
        return module.OM_HUB_CACHE

    @property
    def REGEX_COMMIT_HASH(self):
        module = get_plugin()
        return module.REGEX_COMMIT_HASH

    @property
    def default_cache_path(self):
        module = get_plugin()
        return module.default_cache_path

    @property
    def _CACHED_NO_EXIST(self):
        module = get_plugin()
        return module._CACHED_NO_EXIST

    @property
    def ENDPOINT(self):
        module = get_plugin()
        return module.ENDPOINT

    def upload_file(
        self,
        *,
        path_or_fileobj: Union[str, Path, bytes, BinaryIO],
        path_in_repo: str,
        repo_id: str,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.upload_file(
            path_or_fileobj=path_or_fileobj,
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            token=token,
            revision=revision,
            commit_message=commit_message,
            commit_description=commit_description,
            **kwargs,
        )

    def upload_folder(
        self,
        repo_id: str,
        folder_path: Union[str, Path],
        path_in_repo: Optional[str] = "",
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.upload_folder(
            repo_id=repo_id,
            folder_path=folder_path,
            path_in_repo=path_in_repo,
            commit_message=commit_message,
            commit_description=commit_description,
            token=token,
            revision=revision,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            **kwargs,
        )

    def create_commit(
        self,
        repo_id: str,
        operations: Iterable[CommitOperation],
        *,
        commit_message: str,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        num_threads: int = 5,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.create_commit(
            repo_id=repo_id,
            operations=operations,
            commit_message=commit_message,
            commit_description=commit_description,
            token=token,
            revision=revision,
            num_threads=num_threads,
            **kwargs,
        )

    def om_hub_download(
        self,
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
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.om_hub_download(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            repo_type=repo_type,
            revision=revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
            token=token,
            force_download=force_download,
            resume_download=resume_download,
            local_dir_use_symlinks=local_dir_use_symlinks,
            local_files_only=local_files_only,
            user_agent=user_agent,
            proxies=proxies,
            endpoint=endpoint,
            **kwargs,
        )

    def snapshot_download(
        self,
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
        tqdm_class: Optional[tqdm] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.snapshot_download(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            cache_dir=cache_dir,
            local_dir=local_dir,
            library_name=library_name,
            library_version=library_version,
            token=token,
            force_download=force_download,
            resume_download=resume_download,
            local_dir_use_symlinks=local_dir_use_symlinks,
            local_files_only=local_files_only,
            user_agent=user_agent,
            proxies=proxies,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            max_workers=max_workers,
            tqdm_class=tqdm_class,
            endpoint=endpoint,
            **kwargs,
        )

    def get_om_file_metadata(
        self,
        url: str,
        token: Optional[str] = None,
        proxies: Optional[Dict] = None,
        timeout: Optional[float] = DEFAULT_REQUEST_TIMEOUT,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.get_om_file_metadata(
            url=url,
            token=token,
            proxies=proxies,
            timeout=timeout,
            **kwargs,
        )

    def om_hub_url(
        self,
        repo_id: str,
        filename: str,
        *,
        subfolder: Optional[str] = None,
        revision: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.om_hub_url(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            revision=revision,
            endpoint=endpoint,
            **kwargs,
        )

    def http_get(
        self,
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
        module = get_plugin(kwargs.pop("platform", None))
        return module.http_get(
            url=url,
            temp_file=temp_file,
            proxies=proxies,
            headers=headers,
            displayed_filename=displayed_filename,
            resume_size=resume_size,
            expected_size=expected_size,
            _nb_retries=_nb_retries,
            **kwargs,
        )

    def try_to_load_from_cache(
        self,
        repo_id: str,
        filename: str,
        cache_dir: Union[str, Path, None] = None,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        **kwargs,
    ) -> Union[str, _CACHED_NO_EXIST_T, None]:
        module = get_plugin(kwargs.pop("platform", None))
        return module.try_to_load_from_cache(
            repo_id=repo_id,
            filename=filename,
            cache_dir=cache_dir,
            revision=revision,
            repo_type=repo_type,
        )

    def create_repo(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        private: bool = False,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        space_sdk: Optional[str] = None,
        space_hardware=None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.create_repo(
            repo_id=repo_id,
            token=token,
            private=private,
            repo_type=repo_type,
            exist_ok=exist_ok,
            space_sdk=space_sdk,
            space_hardware=space_hardware,
            **kwargs,
        )

    def delete_repo(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        missing_ok: bool = False,
        **kwargs,
    ) -> None:
        module = get_plugin(kwargs.pop("platform", None))
        return module.delete_repo(
            repo_id=repo_id,
            token=token,
            repo_type=repo_type,
            missing_ok=missing_ok,
        )

    def repo_info(
        self,
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.repo_info(
            repo_id=repo_id,
            repo_type=repo_type,
            timeout=timeout,
            token=token,
            **kwargs,
        )

    def model_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.model_info(
            repo_id=repo_id,
            timeout=timeout,
            token=token,
            **kwargs,
        )

    def list_models(
        self,
        filter=None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.list_models(
            filter=filter,
            author=author,
            token=token,
            limit=limit,
        )

    def dataset_info(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        timeout: Union[int, float] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.dataset_info(
            repo_id=repo_id,
            token=token,
            timeout=timeout,
            **kwargs,
        )

    def list_datasets(
        self,
        filter=None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.list_datasets(filter=filter, author=author, token=token)

    def list_metrics(self, *args, **kwargs):
        module = get_plugin(kwargs.pop("platform", None))
        return module.list_metrics(*args, **kwargs)

    def space_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.space_info(
            repo_id=repo_id,
            timeout=timeout,
            token=token,
            **kwargs,
        )

    def list_spaces(
        self,
        author: Optional[str] = None,
        space_name: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.list_spaces(
            author=author,
            space_name=space_name,
            sort=sort,
            limit=limit,
            token=token,
        )

    def restart_space(self, repo_id: str, token: Optional[str] = None, **kwargs):
        module = get_plugin(kwargs.pop("platform", None))
        return module.restart_space(repo_id=repo_id, token=token)

    def list_repo_tree(
        self,
        repo_id: str,
        path_in_repo: Optional[str] = None,
        *,
        recursive: bool = False,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.list_repo_tree(
            repo_id=repo_id,
            path_in_repo=path_in_repo,
            revision=revision,
            token=token,
            recursive=recursive,
        )

    def whoami(self, token: Optional[str] = None, **kwargs):
        module = get_plugin(kwargs.pop("platform", None))
        return module.whoami(token=token)

    def create_branch(
        self,
        repo_id: str,
        *,
        branch: str,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.create_branch(
            repo_id=repo_id,
            branch=branch,
            revision=revision,
            token=token,
            repo_type=repo_type,
            exist_ok=exist_ok,
        )

    def delete_branch(
        self, repo_id: str, *, branch: str, token: Optional[str] = None, repo_type: Optional[str] = None, **kwargs
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.delete_branch(
            repo_id=repo_id,
            branch=branch,
            token=token,
            repo_type=repo_type,
        )

    def get_full_repo_name(
        self, model_id: str, *, organization: Optional[str] = None, token: Optional[str] = None, **kwargs
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.get_full_repo_name(model_id=model_id, organization=organization, token=token)

    def metadata_update(
        self,
        repo_id: str,
        metadata: Dict,
        *,
        repo_type: Optional[str] = None,
        overwrite: bool = False,
        token: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.metadata_update(
            repo_id=repo_id,
            metadata=metadata,
            repo_type=repo_type,
            overwrite=overwrite,
            token=token,
            commit_message=commit_message,
            commit_description=commit_description,
            revision=revision,
        )

    def om_raise_for_status(self, response, endpoint_name: Optional[str] = None, **kwargs):
        module = get_plugin(kwargs.pop("platform", None))
        return module.om_raise_for_status(response=response, endpoint_name=endpoint_name)

    def build_om_headers(
        self,
        token: Optional[str] = None,
        is_write_action: bool = False,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Union[Dict, str, None] = None,
        **kwargs,
    ):
        module = get_plugin(kwargs.pop("platform", None))
        return module.build_om_headers(
            token=token,
            is_write_action=is_write_action,
            library_name=library_name,
            library_version=library_version,
            user_agent=user_agent,
        )


api = HubApi()

OM_HOME = api.OM_HOME
OM_HUB_CACHE = api.OM_HUB_CACHE
REGEX_COMMIT_HASH = api.REGEX_COMMIT_HASH
default_cache_path = api.default_cache_path
_CACHED_NO_EXIST = api._CACHED_NO_EXIST
ENDPOINT = api.ENDPOINT
upload_file = api.upload_file
upload_folder = api.upload_folder
create_commit = api.create_commit
om_hub_download = api.om_hub_download
snapshot_download = api.snapshot_download
get_om_file_metadata = api.get_om_file_metadata
om_hub_url = api.om_hub_url
http_get = api.http_get
try_to_load_from_cache = api.try_to_load_from_cache
create_repo = api.create_repo
delete_repo = api.delete_repo
repo_info = api.repo_info
model_info = api.model_info
list_models = api.list_models
dataset_info = api.dataset_info
list_datasets = api.list_datasets
list_metrics = api.list_metrics
space_info = api.space_info
list_spaces = api.list_spaces
restart_space = api.restart_space
list_repo_tree = api.list_repo_tree
whoami = api.whoami
create_branch = api.create_branch
delete_branch = api.delete_branch
get_full_repo_name = api.get_full_repo_name
om_raise_for_status = api.om_raise_for_status
build_om_headers = api.build_om_headers
OmApi = api.OmApi
RepoUrl = api.RepoUrl
RepoFile = api.RepoFile
RepoFolder = api.RepoFolder
ModelInfo = api.ModelInfo
ModelFilter = api.ModelFilter
DatasetInfo = api.DatasetInfo
CommitOperationAdd = api.CommitOperationAdd
CommitOperationDelete = api.CommitOperationDelete
Repository = api.Repository
DatasetCard = api.DatasetCard
DatasetCardData = api.DatasetCardData
metadata_update = api.metadata_update
OmFileSystem = api.OmFileSystem
OmHubHTTPError = api.OmHubHTTPError
GatedRepoError = api.GatedRepoError
OMValidationError = api.OMValidationError
EntryNotFoundError = api.EntryNotFoundError
AccessWhiteListError = api.AccessWhiteListError
RevisionNotFoundError = api.RevisionNotFoundError
RepositoryNotFoundError = api.RepositoryNotFoundError
LocalEntryNotFoundError = api.LocalEntryNotFoundError
