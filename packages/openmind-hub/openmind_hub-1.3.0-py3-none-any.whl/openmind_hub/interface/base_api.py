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
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union, BinaryIO, Optional, List, Iterable, Literal, Dict, Any

from requests import Response, HTTPError
from tqdm.auto import tqdm as base_tqdm

from .dependent_methods import (
    DEFAULT_REQUEST_TIMEOUT,
    _CACHED_NO_EXIST_T,
    CommitInfo,
    OmFileMetadata,
    SpaceHardware,
    SpaceInfo,
    RepoSibling,
    BlobLfsInfo,
    LastCommitInfo,
)

default_home = str(Path.home() / ".cache")
OM_HOME = os.path.join(os.getenv("XDG_CACHE_HOME", default_home), "openmind")
OM_HUB_CACHE = os.path.join(OM_HOME, "hub")
REGEX_COMMIT_HASH = None
default_cache_path = None
_CACHED_NO_EXIST = None
ENDPOINT = None


class OmApi:
    """OmApi类"""


@dataclass
class ModelFilter:
    """模型搜索条件"""


@dataclass
class ModelInfo:
    id: str
    name: str
    owner: str
    fullname: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    downloads: int
    likes: int
    private: Optional[Union[bool, None]]
    library_name: Optional[str]
    tags: List[str]
    pipeline_tag: Optional[str]


@dataclass
class DatasetInfo:
    id: str
    owner: Optional[str]
    sha: Optional[str]
    created_at: Optional[datetime]
    last_modified: Optional[datetime]
    private: Optional[Union[bool, None]]
    disabled: Optional[bool]
    downloads: int
    likes: int
    tags: List[str]
    siblings: Optional[List[RepoSibling]]


class RepoUrl(str):
    def __new__(cls, url: Any, endpoint: Optional[str] = None):
        return super(RepoUrl, cls).__new__(cls, url)


@dataclass
class RepoFile:
    path: str
    size: int
    blob_id: str
    lfs: Optional[BlobLfsInfo] = None
    last_commit: Optional[LastCommitInfo] = None


@dataclass
class RepoFolder:
    path: str
    last_commit: Optional[LastCommitInfo] = None


@dataclass
class CommitOperationAdd:
    """封装要上传的文件信息，传递给create_commit"""

    path_in_repo: str
    path_or_fileobj: Union[str, Path, bytes, BinaryIO]


@dataclass
class CommitOperationDelete:
    """封装要删除的文件信息，传递给create_commit"""

    path_in_repo: str
    is_folder: Union[bool, Literal["auto"]] = "auto"


class Repository:
    """封装一系列git命令"""


class DatasetCard:
    """数据集仓库卡片"""


class DatasetCardData:
    """仓库卡片元数据"""


class OmFileSystem:
    """文件管理系统"""


class OmHubHTTPError(HTTPError):
    """所有HTTP异常的父类"""


class RepositoryNotFoundError(OmHubHTTPError):
    """仓库不存在"""


class RevisionNotFoundError(OmHubHTTPError):
    """分支或版本不存在"""


class EntryNotFoundError(OmHubHTTPError, FileNotFoundError):
    """文件不存在"""


class GatedRepoError(OmHubHTTPError):
    """仓库限制访问"""


class LocalEntryNotFoundError(EntryNotFoundError, FileNotFoundError, ValueError):
    """本地文件不存在"""


class OMValidationError(ValueError):
    """参数校验失败"""


class AccessWhiteListError(OmHubHTTPError):
    """418白名单"""


CommitOperation = Union[CommitOperationAdd, CommitOperationDelete]


class BaseApi:
    OmApi = OmApi
    RepoUrl = RepoUrl
    RepoFile = RepoFile
    RepoFolder = RepoFolder
    ModelInfo = ModelInfo
    ModelFilter = ModelFilter
    DatasetInfo = DatasetInfo
    CommitOperationAdd = CommitOperationAdd
    CommitOperationDelete = CommitOperationDelete
    Repository = Repository
    DatasetCard = DatasetCard
    DatasetCardData = DatasetCardData
    OmFileSystem = OmFileSystem
    OmHubHTTPError = OmHubHTTPError
    GatedRepoError = GatedRepoError
    OMValidationError = OMValidationError
    EntryNotFoundError = EntryNotFoundError
    AccessWhiteListError = AccessWhiteListError
    RevisionNotFoundError = RevisionNotFoundError
    RepositoryNotFoundError = RepositoryNotFoundError
    LocalEntryNotFoundError = LocalEntryNotFoundError

    @property
    @abstractmethod
    def OM_HOME(self):
        return OM_HOME

    @property
    @abstractmethod
    def OM_HUB_CACHE(self):
        return OM_HUB_CACHE

    @property
    @abstractmethod
    def REGEX_COMMIT_HASH(self):
        return REGEX_COMMIT_HASH

    @property
    @abstractmethod
    def default_cache_path(self):
        return default_cache_path

    @property
    @abstractmethod
    def _CACHED_NO_EXIST(self):
        return _CACHED_NO_EXIST

    @property
    @abstractmethod
    def ENDPOINT(self):
        return ENDPOINT

    @abstractmethod
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
        """上传单个文件"""
        raise NotImplementedError()

    @abstractmethod
    def upload_folder(
        self,
        *,
        repo_id: str,
        folder_path: Union[str, Path],
        path_in_repo: Optional[str] = "",
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        num_threads: int = 5,
        **kwargs,
    ):
        """上传目录中的文件"""
        raise NotImplementedError()

    @abstractmethod
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
    ) -> CommitInfo:
        """上传单个或多个文件，文件信息封装在operations中"""
        raise NotImplementedError()

    @abstractmethod
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
    ) -> str:
        """下载仓库内某个文件，返回本地文件路径"""
        raise NotImplementedError()

    @abstractmethod
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
        tqdm_class: Optional[base_tqdm] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ) -> str:
        """下载仓库内文件，返回本地目录路径"""
        raise NotImplementedError()

    @abstractmethod
    def get_om_file_metadata(
        self,
        url: str,
        token: Optional[str] = None,
        proxies: Optional[Dict] = None,
        timeout: Optional[float] = DEFAULT_REQUEST_TIMEOUT,
        **kwargs,
    ) -> OmFileMetadata:
        """获取文件元数据信息"""
        raise NotImplementedError()

    @abstractmethod
    def om_hub_url(
        self,
        repo_id: str,
        filename: str,
        *,
        subfolder: Optional[str] = None,
        revision: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ) -> str:
        """返回文件下载的url链接"""
        raise NotImplementedError()

    @abstractmethod
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
        """发起get请求，用于下载文件"""
        raise NotImplementedError()

    @abstractmethod
    def try_to_load_from_cache(
        self,
        repo_id: str,
        filename: str,
        cache_dir: Union[str, Path, None] = None,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
    ) -> Union[str, _CACHED_NO_EXIST_T, None]:
        """查找文件在缓存中的路径，若不存在则返回`None`"""
        raise NotImplementedError()

    @abstractmethod
    def create_repo(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        private: bool = False,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
        desc: Optional[str] = None,
        fullname: Optional[str] = None,
        space_sdk: Optional[str] = None,
        space_hardware: Optional[SpaceHardware] = None,
        space_image: Optional[str] = None,
        license: str = "apache-2.0",
        **kwargs,
    ) -> RepoUrl:
        """创建仓库，包括模型、数据集和体验空间"""
        raise NotImplementedError()

    @abstractmethod
    def delete_repo(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        missing_ok: bool = False,
    ) -> None:
        """删除仓库，包括模型、数据集和体验空间"""
        raise NotImplementedError()

    @abstractmethod
    def repo_info(
        self,
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Union[ModelInfo, DatasetInfo, SpaceInfo]:
        """获取仓库信息"""
        raise NotImplementedError()

    @abstractmethod
    def model_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> ModelInfo:
        """获取模型信息"""
        raise NotImplementedError()

    @abstractmethod
    def list_models(
        self,
        filter: Union[ModelFilter, None] = None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> Iterable[ModelInfo]:
        """搜索模型"""
        raise NotImplementedError()

    @abstractmethod
    def dataset_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> DatasetInfo:
        """获取数据集信息"""
        raise NotImplementedError()

    @abstractmethod
    def list_datasets(
        self,
        filter: Union[ModelFilter, None] = None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[DatasetInfo]:
        """搜索数据集"""
        raise NotImplementedError()

    @abstractmethod
    def list_metrics(self):
        raise NotImplementedError()

    @abstractmethod
    def space_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> SpaceInfo:
        """获取体验空间信息"""
        raise NotImplementedError()

    @abstractmethod
    def list_spaces(
        self,
        author: Optional[str] = None,
        space_name: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[SpaceInfo]:
        """搜索体验空间"""
        raise NotImplementedError()

    @abstractmethod
    def restart_space(self, repo_id: str, token: Optional[str] = None, **kwargs):
        """重启体验空间app"""
        raise NotImplementedError()

    @abstractmethod
    def list_repo_tree(
        self,
        repo_id: str,
        path_in_repo: Optional[str] = None,
        *,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[Union[RepoFile, RepoFolder]]:
        """列出仓库内的文件"""
        raise NotImplementedError()

    @abstractmethod
    def whoami(self, token: Optional[str] = None) -> Dict:
        """获取用户信息，包括用户名和邮箱"""
        raise NotImplementedError()

    @abstractmethod
    def create_branch(
        self,
        repo_id: str,
        *,
        branch: str,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        exist_ok: bool = False,
    ) -> None:
        """创建分支"""
        raise NotImplementedError()

    @abstractmethod
    def delete_branch(
        self,
        repo_id: str,
        *,
        branch: str,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
    ) -> None:
        """删除分支"""
        raise NotImplementedError()

    @abstractmethod
    def get_full_repo_name(
        self,
        model_id: str,
        *,
        organization: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """拼接完整仓库名"""
        raise NotImplementedError()

    @abstractmethod
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
    ) -> str:
        """更新仓库卡片"""
        raise NotImplementedError()

    @abstractmethod
    def om_raise_for_status(self, response: Response, endpoint_name: Optional[str] = None) -> None:
        """根据响应体的状态码抛出对应异常"""
        raise NotImplementedError()

    @abstractmethod
    def build_om_headers(
        self,
        *,
        token: Optional[str] = None,
        is_write_action: bool = False,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Union[Dict, str, None] = None,
    ) -> Dict[str, str]:
        """构建请求头"""
        raise NotImplementedError()


base_api = BaseApi()

upload_file = base_api.upload_file
upload_folder = base_api.upload_folder
create_commit = base_api.create_commit
om_hub_download = base_api.om_hub_download
snapshot_download = base_api.snapshot_download
get_om_file_metadata = base_api.get_om_file_metadata
om_hub_url = base_api.om_hub_url
http_get = base_api.http_get
try_to_load_from_cache = base_api.try_to_load_from_cache
create_repo = base_api.create_repo
delete_repo = base_api.delete_repo
repo_info = base_api.repo_info
model_info = base_api.model_info
list_models = base_api.list_models
dataset_info = base_api.dataset_info
list_datasets = base_api.list_datasets
list_metrics = base_api.list_metrics
space_info = base_api.space_info
list_spaces = base_api.list_spaces
restart_space = base_api.restart_space
list_repo_tree = base_api.list_repo_tree
whoami = base_api.whoami
create_branch = base_api.create_branch
delete_branch = base_api.delete_branch
get_full_repo_name = base_api.get_full_repo_name
metadata_update = base_api.metadata_update
om_raise_for_status = base_api.om_raise_for_status
build_om_headers = base_api.build_om_headers
