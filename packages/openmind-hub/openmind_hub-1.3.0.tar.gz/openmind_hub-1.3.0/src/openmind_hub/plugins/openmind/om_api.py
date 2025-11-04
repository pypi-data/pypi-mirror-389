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
import base64
import gc
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import re
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    BinaryIO,
)
from urllib.parse import quote, urlparse, urlencode

from requests import HTTPError
from tqdm.auto import tqdm as base_tqdm

from .repocard_data import DatasetCardData
from ._commit_api import (
    CommitOperationAdd,
    _fetch_upload_modes,
    _prepare_commit_payload,
    _upload_lfs_files,
    _warn_on_overwriting_operations,
    CommitOperationDelete,
    CommitOperation,
)
from .constants import (
    NOT_FILE_CODE,
    CREATE_COMMIT_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_REVISION,
    DUPLICATE_CREATING_CODE,
    ENDPOINT,
    IGNORE_GIT_FOLDER_PATTERNS,
    REPO_TYPE_MODEL,
    REPO_TYPES,
    REPO_TYPES_MAPPING,
    SPACES_IMAGES,
    SPACES_SDK_TYPES,
)
from .file_download import check_admin
from .utils import (
    build_om_headers,
    logging,
    om_raise_for_status,
    OmHubHTTPError,
    RepositoryNotFoundError,
)
from .utils.logging import replace_invalid_characters
from .utils._http import get_session
from .utils._path import filter_repo_objects
from .utils._validators import validate_om_hub_args


logger = logging.get_logger(__name__)


def repo_type_and_id_from_om_id(om_id: str, hub_url: Optional[str] = None) -> Tuple[Optional[str], Optional[str], str]:
    """
    Returns the repo type and ID from a URL linking to a repository

    Args:
        om_id (`str`):
            An URL or ID of a repository on the hub.
        hub_url (`str`, *optional*):
            The URL of the Hub, defaults to the ENDPOINT in constants.py.

    Returns:
        A tuple with three items: repo_type (`str` or `None`), namespace (`str` or
        `None`) and repo_id (`str`).

    Raises:
        - [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If URL cannot be parsed.
        - [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)
            If `repo_type` is unknown.
    """
    input_om_id = om_id
    hub_url = re.sub(r"https?://", "", hub_url if hub_url is not None else ENDPOINT)
    is_om_url = hub_url in om_id and "@" not in om_id

    url_segments = om_id.split("/")
    is_om_id = len(url_segments) <= 3

    namespace: Optional[str]
    if is_om_url:
        namespace, repo_id = url_segments[-2:]
        if namespace == hub_url:
            namespace = None
        if len(url_segments) > 2 and hub_url not in url_segments[-3]:
            repo_type = url_segments[-3]
        elif namespace in REPO_TYPES_MAPPING:
            # Mean canonical dataset or model
            repo_type = REPO_TYPES_MAPPING[namespace]
            namespace = None
        else:
            repo_type = None
    elif is_om_id:
        if len(url_segments) == 3:
            # Passed <repo_type>/<user>/<model_id> or <repo_type>/<org>/<model_id>
            repo_type, namespace, repo_id = url_segments[-3:]
        elif len(url_segments) == 2:
            if url_segments[0] in REPO_TYPES_MAPPING:
                # Passed '<model_id>' or 'datasets/<dataset_id>' for a canonical model or dataset
                repo_type = REPO_TYPES_MAPPING[url_segments[0]]
                namespace = None
                repo_id = om_id.split("/")[-1]
            else:
                # Passed <user>/<model_id> or <org>/<model_id>
                namespace, repo_id = om_id.split("/")[-2:]
                repo_type = None
        else:
            # Passed <model_id>
            repo_id = url_segments[0]
            namespace, repo_type = None, None
    else:
        error_msg = f"Unable to retrieve user and repo ID from the passed OM ID: {om_id}"
        raise ValueError(replace_invalid_characters(error_msg))

    if repo_type in REPO_TYPES_MAPPING:
        repo_type = REPO_TYPES_MAPPING[repo_type]
    if repo_type == "":
        repo_type = None
    if repo_type not in REPO_TYPES:
        error_msg = f"Unknown `repo_type`: '{repo_type}' ('{input_om_id}')"
        raise ValueError(replace_invalid_characters(error_msg))

    return repo_type, namespace, repo_id


@dataclass
class LastCommitInfo(dict):
    oid: str
    title: str
    date: datetime

    def __post_init__(self):  # hack to make LastCommitInfo backward compatible
        self.update(asdict(self))


@dataclass
class BlobLfsInfo(dict):
    size: int
    sha256: str

    def __post_init__(self):  # hack to make BlobLfsInfo backward compatible
        self.update(asdict(self))


@dataclass
class RepoSibling:
    """
    Contains basic information about a repo file inside a repo on the Hub.

    Attributes:
        rfilename (str):
            file name, relative to the repo root.
        size (`int`, *optional*):
            The file's size, in bytes. This attribute is defined when `files_metadata` argument of [`repo_info`] is set
            to `True`. It's `None` otherwise.
        blob_id (`str`, *optional*):
            The file's git OID. This attribute is defined when `files_metadata` argument of [`repo_info`] is set to
            `True`. It's `None` otherwise.
    """

    rfilename: str
    size: Optional[int] = None
    blob_id: Optional[str] = None


@dataclass
class RepoFile:
    """
    Contains information about a file on the Hub.

    Attributes:
        path (str):
            File path relative to the repo root.
        size (`int`):
            The file's size, in bytes.
        lfs (`bool`):
            Lfs file's metadata, or None.
    """

    path: str
    size: int
    blob_id: str
    lfs: Optional[BlobLfsInfo] = None
    last_commit: Optional[LastCommitInfo] = None

    def __init__(self, **kwargs):
        self.path = kwargs.pop("path", "")
        self.size = kwargs.pop("size", 0)
        self.blob_id = kwargs.pop("etag", "")
        if kwargs.pop("is_lfs"):
            self.lfs = BlobLfsInfo(size=self.size, sha256=self.blob_id)
        else:
            self.lfs = None
        last_commit = kwargs.pop("commit", {})
        if last_commit:
            update_at = last_commit.get("created", "")
            if update_at.endswith("Z"):
                update_at = datetime.fromisoformat(update_at[:-1])
            elif update_at.endswith("+08:00"):
                update_at = datetime.fromisoformat(update_at[:-6])
            else:
                update_at = datetime.fromisoformat(update_at)
            self.last_commit = LastCommitInfo(
                oid=last_commit.get("commit_sha"), title=last_commit.get("message"), date=update_at
            )
        else:
            self.last_commit = None

        self.rfilename = self.path
        self.lastCommit = self.last_commit


@dataclass
class RepoFolder:
    """
    Contains information about a folder on the Hub.

    Attributes:
        path (str):
            Folder path relative to the repo root.
    """

    path: str
    last_commit: Optional[LastCommitInfo] = None

    def __init__(self, **kwargs):
        self.path = kwargs.pop("path", "")
        last_commit = kwargs.pop("commit", {})
        if last_commit:
            update_at = last_commit.get("created", "")
            if update_at.endswith("Z"):
                update_at = datetime.fromisoformat(update_at[:-1])
            elif update_at.endswith("+08:00"):
                update_at = datetime.fromisoformat(update_at[:-6])
            else:
                update_at = datetime.fromisoformat(update_at)
            self.last_commit = LastCommitInfo(
                oid=last_commit.get("commit_sha"), title=last_commit.get("message"), date=update_at
            )
        else:
            self.last_commit = None


@dataclass
class ModelInfo:
    """
    Contains information about a model on the Hub.

    <Tip>

    Most attributes of this class are optional. This is because the data returned by the Hub depends on the query made.
    In general, the more specific the query, the more information is returned.

    </Tip>

    Attributes:
        id (`str`):
            ID of model.
        name (`str`):
            Name of model.
        owner (`str`):
            Owner of model, user or organization.
        created_at (`datetime`, *optional*):
            Date of creation of the repo on the Hub.
        last_modified (`datetime`, *optional*):
            Date of last update of the repo on the Hub.
        downloads (`int`):
            Number of downloads of the model.
        likes (`int`):
            Number of likes of the model.
        fullname (`str`):
            Fullname of model.
        private (`bool`, *optional*):
            Is the repo private.
        library_name (`str`, *optional*):
            Library associated with the model.
        tags (`List[str]`):
            List of tags of the model.
        pipeline_tag (`str`, *optional*):
            Pipeline tag associated with the model.
        siblings (`List[RepoSibling]`):
            List of [`openmind_hub.om_api.RepoSibling`] objects that constitute the Model.
    """

    id: str
    name: Optional[str]
    owner: Optional[str]
    fullname: Optional[str]
    created_at: Optional[datetime]
    last_modified: Optional[datetime]
    downloads: Optional[int]
    likes: Optional[int]
    private: Optional[Union[bool, None]]
    library_name: Optional[str]
    tags: Optional[List[str]]
    pipeline_tag: Optional[str]
    siblings: Optional[List[RepoSibling]]
    extra: Optional[List[dict]]

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", "")
        self.name = kwargs.pop("name", "")
        self.owner = kwargs.pop("owner", "")
        self.fullname = kwargs.pop("fullname", "")
        self.created_at = kwargs.pop("create_at", None)
        self.last_modified = kwargs.pop("updated_at", None)
        self.downloads = kwargs.pop("download_count", 0)
        self.likes = kwargs.pop("like_count", 0)
        self.extra = kwargs.pop("extra", [])
        visibility = kwargs.pop("visibility", None)
        if visibility == "private":
            self.private = True
        elif visibility == "public":
            self.private = False
        else:
            self.private = None
        if "labels" in kwargs:
            labels = kwargs.get("labels")
            self.tags = labels.pop("others", [])
            self.pipeline_tag = labels.pop("task", None)
            library_name = labels.pop("frameworks", [])
            if library_name:
                self.library_name = ", ".join(library_name)
            else:
                self.library_name = None
        else:
            self.tags = kwargs.pop("others", [])
            self.pipeline_tag = kwargs.pop("task", None)
            library_name = kwargs.pop("frameworks", [])
            if library_name:
                self.library_name = ", ".join(library_name)
            else:
                self.library_name = None
        siblings = kwargs.pop("siblings", [])
        self.siblings = [RepoSibling(rfilename=sibling.get("rfilename")) for sibling in siblings] if siblings else []


@dataclass
class ModelCiInfo:
    total: int
    model_ci: list

    def __init__(self, **kwargs):
        self.total = kwargs.pop("total", 0)
        self.model_ci = kwargs.pop("model_ci", [])


@dataclass
class DatasetInfo:
    """
    Contains information about a dataset on the Hub.

    <Tip>

    Most attributes of this class are optional. This is because the data returned by the Hub depends on the query made.
    In general, the more specific the query, the more information is returned.

    </Tip>

    Attributes:
        id (`str`):
            ID of dataset.
        name (`str`):
            Name of dataset.
        owner (`str`):
            Owner of dataset, user or organization.
        sha (`str`):
            Repo SHA at this particular revision.
        created_at (`datetime`, *optional*):
            Date of creation of the repo on the Hub.
        last_modified (`datetime`, *optional*):
            Date of last commit to the repo.
        fullname (`str`):
            Fullname of dataset.
        private (`bool`, *optional*):
            Is the repo private.
        downloads (`int`):
            Number of downloads of the dataset.
        likes (`int`):
            Number of likes of the dataset.
        library_name (`str`, *optional*):
            Library associated with the dataset.
        tags (`List[str]`):
            List of tags of the dataset.
        pipeline_tag (`str`, *optional*):
            Pipeline tag associated with the dataset.
        card_data (`DatasetCardData`, *optional*)
            Dataset Card Metadata.
        library_name (`str`, *optional*):
            Library associated with the dataset.
        pipeline_tag (`str`, *optional*):
            Pipeline tag associated with the dataset.
        siblings (`List[RepoSibling]`):
            List of [`openmind_hub.om_api.RepoSibling`] objects that constitute the Dataset.
    """

    id: str
    owner: Optional[str]
    sha: Optional[str]
    created_at: Optional[datetime]
    last_modified: Optional[datetime]
    private: Optional[Union[bool, None]]
    disabled: Optional[bool]
    downloads: Optional[int]
    likes: Optional[int]
    library_name: Optional[str]
    tags: Optional[List[str]]
    pipeline_tag: Optional[str]
    card_data: Optional[DatasetCardData]
    siblings: Optional[List[RepoSibling]]

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", "")
        self.name = kwargs.pop("name", None)
        self.owner = kwargs.pop("author", None)
        self.fullname = kwargs.pop("fullname", None)
        self.sha = kwargs.pop("sha", None)
        self.created_at = kwargs.pop("create_at", None)
        self.last_modified = kwargs.pop("updated_at", None)
        visibility = kwargs.pop("visibility", None)
        if visibility == "private":
            self.private = True
        elif visibility == "public":
            self.private = False
        else:
            self.private = None
        self.disabled = kwargs.pop("disable", None)
        self.downloads = kwargs.pop("download_count", 0)
        self.likes = kwargs.pop("like_count", 0)
        card_data = kwargs.pop("cardData", None) or kwargs.pop("card_data", None)
        self.card_data = (
            DatasetCardData(**card_data, ignore_metadata_errors=True) if isinstance(card_data, dict) else card_data
        )
        siblings = kwargs.pop("siblings", [])
        self.siblings = [RepoSibling(rfilename=sibling.get("rfilename")) for sibling in siblings] if siblings else []
        if "labels" in kwargs:
            labels = kwargs.pop("labels")
            self.tags = labels.pop("others", [])
            self.pipeline_tag = labels.pop("task", None)
            self.library_name = labels.pop("frameworks", None)
        else:
            self.tags = kwargs.pop("others", [])
            self.pipeline_tag = kwargs.pop("task", None)
            self.library_name = kwargs.pop("frameworks", None)

        self.__dict__.update(**kwargs)


@dataclass
class SpaceInfo:
    """
    Contains information about a space on the Hub.

    <Tip>

    Most attributes of this class are optional. This is because the data returned by the Hub depends on the query made.
    In general, the more specific the query, the more information is returned.

    </Tip>

    Attributes:
        id (`str`):
            ID of space.
        name (`str`):
            Name of space.
        owner (`str`):
            Owner of space, user or organization.
        fullname (`str`):
            Fullname of space.
        private (`bool`, *optional*):
            Is the repo private.
        library_name (`str`, *optional*):
            Library associated with the space.
        tags (`List[str]`):
            List of tags of the space. Compared to `card_data.tags`, contains extra tags computed by the Hub.
        pipeline_tag (`str`, *optional*):
            Pipeline tag associated with the space.
        siblings (`List[RepoSibling]`):
            List of [`openmind_hub.om_api.RepoSibling`] objects that constitute the Space.
    """

    id: str
    name: str
    owner: str
    fullname: Optional[str]
    private: Optional[Union[bool, None]]
    library_name: Optional[str]
    tags: Optional[List[str]]
    pipeline_tag: Optional[str]
    siblings: Optional[List[RepoSibling]]

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", "")
        self.name = kwargs.pop("name", "")
        self.owner = kwargs.pop("owner", "")
        self.fullname = kwargs.pop("fullname", "")
        visibility = kwargs.pop("visibility", None)
        if visibility == "private":
            self.private = True
        elif visibility == "public":
            self.private = False
        else:
            self.private = None
        siblings = kwargs.pop("siblings", [])
        self.siblings = [RepoSibling(rfilename=sibling.get("rfilename")) for sibling in siblings] if siblings else []
        labels = kwargs.get("labels")
        if labels is not None:
            self.tags = labels.pop("others", [])
            self.pipeline_tag = labels.pop("task", None)
            library_name = labels.pop("frameworks", [])
            if library_name:
                self.library_name = ", ".join(library_name)
            else:
                self.library_name = None
        else:
            self.tags = kwargs.pop("others", [])
            self.pipeline_tag = kwargs.pop("task", None)
            library_name = kwargs.pop("frameworks", [])
            if library_name:
                self.library_name = ", ".join(library_name)
            else:
                self.library_name = None

        self.__dict__.update(**kwargs)


class SpaceHardware(str, Enum):
    """Enumeration of hardware available to run your Space on the Hub."""

    CPU = "CPU basic 2 vCPU · 16GB · FREE"
    NPU = "NPU basic 16 vCPU · 128GB · FREE"


@dataclass
class MetricInfo:
    """
    Contains information about a metric on the Hub.

    Attributes:
        id (`str`):
            ID of the metric. E.g. `"accuracy"`.
        space_id (`str`):
            ID of the space associated with the metric. E.g. `"Accuracy"`.
        description (`str`):
            Description of the metric.
    """

    id: str
    space_id: str
    description: Optional[str]

    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", "")
        self.space_id = kwargs.pop("spaceId", "")
        self.description = kwargs.pop("desc", None)
        # backwards compatibility
        self.__dict__.update(**kwargs)


@dataclass
class ModelFilter:
    """
    A class that converts human-readable model search parameters into ones
    compatible with the REST API. For all parameters capitalization does not
    matter.

    Args:
        author (`str`, *optional*):
            A string that can be used to identify models on the Hub by the
            original uploader (author or organization).
        library (`str` or `List`, *optional*):
            A string or list of strings of foundational libraries models were
            originally trained from, such as PyTorch or MindSpore.
        model_name (`str`, *optional*):
            A string that contain complete or partial names for models on the
            Hub, such as "bert" or "bert-base-cased"
        task (`str` or `List`, *optional*):
            A string or list of strings of tasks models were designed for, such
            as: "feature-extraction" or "text-classification"
        tags (`str` or `List`, *optional*):
            A string tag or a list of tags to filter models on the Hub by.
        license (`str`, *optional*):
            License of models.
        sort_by (`str`, *optional*):
            Sort types: most_likes, most_downloads or recently_updated.
        limit (`int`, *optional*):
            Count per page.
    """

    author: Optional[str] = None
    library: Optional[Union[str, List[str]]] = None
    model_name: Optional[str] = None
    task: Optional[Union[str, List[str]]] = None
    tags: Optional[Union[str, List[str]]] = None
    license: Optional[str] = None
    sort_by: Optional[str] = None
    limit: Optional[int] = None


@dataclass
class DatasetFilter:
    author: Optional[str] = None
    benchmark: Optional[Union[str, List[str]]] = None
    dataset_name: Optional[str] = None
    language_creators: Optional[Union[str, List[str]]] = None
    language: Optional[Union[str, List[str]]] = None
    multilinguality: Optional[Union[str, List[str]]] = None
    size_categories: Optional[Union[str, List[str]]] = None
    task_categories: Optional[Union[str, List[str]]] = None
    task_ids: Optional[Union[str, List[str]]] = None


@dataclass
class CommitInfo:
    """Data structure containing information about a newly created commit.

    Returned by [`create_commit`].

    Attributes:
        commit_url (`str`):
            Url where to find the commit.

        commit_message (`str`):
            The summary (first line) of the commit that has been created.

        commit_description (`str`):
            Description of the commit that has been created. Can be empty.

        oid (`str`):
            Commit hash id. Example: `"91c54ad1727ee830252e457677f467be0bfd8a57"`.
    """

    commit_url: str
    commit_message: str
    commit_description: str
    oid: str


class RepoUrl(str):
    """Subclass of `str` describing a repo URL on the Hub.

    `RepoUrl` is returned by `OmApi.create_repo`. It inherits from `str` for backward
    compatibility. At initialization, the URL is parsed to populate properties:
    - endpoint (`str`)
    - namespace (`Optional[str]`)
    - repo_name (`str`)
    - repo_id (`str`)
    - repo_type (`Literal["model", "dataset", "space"]`)
    - url (`str`)

    Args:
        url (`Any`):
            String value of the repo url.
        endpoint (`str`, *optional*):
            Endpoint of the Hub.

    Raises:
        - [`ValueError`]
            If URL cannot be parsed.
        - [`ValueError`]
            If `repo_type` is unknown.
    """

    def __new__(cls, url: Any, endpoint: Optional[str] = None):
        return super(RepoUrl, cls).__new__(cls, url)

    def __init__(self, url: Any, endpoint: Optional[str] = None) -> None:
        super().__init__()
        # Parse URL
        self.endpoint = endpoint or ENDPOINT
        repo_type, namespace, repo_name = repo_type_and_id_from_om_id(self, hub_url=self.endpoint)

        # Populate fields
        self.namespace = namespace
        self.repo_name = repo_name
        self.repo_id = repo_name if not namespace else f"{namespace}/{repo_name}"
        self.repo_type = repo_type or REPO_TYPE_MODEL
        self.url = str(self)  # just in case it's needed

    def __repr__(self) -> str:
        return f"RepoUrl('{self}', endpoint='{self.endpoint}', repo_type='{self.repo_type}', repo_id='{self.repo_id}')"


def _prepare_upload_folder_additions(
    folder_path: Union[str, Path],
    path_in_repo: str,
    allow_patterns: Optional[Union[List[str], str]] = None,
    ignore_patterns: Optional[Union[List[str], str]] = None,
) -> List[CommitOperationAdd]:
    """Generate the list of Add operations for a commit to upload a folder.

    Files not matching the `allow_patterns` (allowlist) and `ignore_patterns` (denylist)
    constraints are discarded.
    """
    folder_path = Path(folder_path).expanduser().resolve()
    if not folder_path.is_dir():
        error_msg = f"Provided path: '{folder_path}' is not a directory"
        raise ValueError(replace_invalid_characters(error_msg))

    # List files from folder
    relpath_to_abspath = {
        path.relative_to(folder_path).as_posix(): path
        for path in sorted(folder_path.glob("**/*"))  # sorted to be deterministic
        if path.is_file()
    }

    # Filter files and return
    # Patterns are applied on the path relative to `folder_path`. `path_in_repo` is prefixed after the filtering.
    prefix = f"{path_in_repo.strip('/')}/" if path_in_repo else ""

    filter_generator = filter_repo_objects(
        relpath_to_abspath.keys(), allow_patterns=allow_patterns, ignore_patterns=ignore_patterns
    )
    return [
        CommitOperationAdd(
            path_or_fileobj=relpath_to_abspath[relpath],  # absolute path on disk
            path_in_repo=prefix + relpath,  # "absolute" path in repo
        )
        for relpath in filter_generator
    ]


class OmApi:
    @validate_om_hub_args
    def __init__(
        self,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Union[Dict, str, None] = None,
    ) -> None:
        """Create an OM client to interact with the Hub via HTTP.

        The client is initialized with some high-level settings used in all requests
        made to the Hub (openMind endpoint, authentication, user agents...).

        Args:
            token (`str`):
                openMind token.
            library_name (`str`, *optional*):
                The name of the library that is making the HTTP request. Will be
                added to the user-agent header.
            library_version (`str`, *optional*):
                The version of the library that is making the HTTP request. Will be
                added to the user-agent header. Example: `"4.24.0"`.
            user_agent (`str`, `dict`, *optional*):
                The user agent info in the form of a dictionary or a single string.
                It will be completed with information about the installed packages.
        """
        self.endpoint = endpoint or ENDPOINT
        if urlparse(self.endpoint).scheme != "https":
            logger.error("Insecure scheme detected, exiting.")
            raise ValueError("Insecure scheme detected, exiting.")
        self.token = token
        self.library_name = library_name
        self.library_version = library_version
        self.user_agent = user_agent
        self._thread_pool: Optional[ThreadPoolExecutor] = None

    def whoami(self, token: Optional[str] = None) -> Dict:
        """
        Args:
            token (`str`, *optional*):
                openMind hub token. Will default to the locally saved token if
                not provided.
        """
        path = f"{self.endpoint}/api/v1/user"
        headers = self.build_om_headers(token=token or self.token)
        logger.info("_fetch_upload_modes send HTTPS request")
        r = get_session().get(path, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        try:
            om_raise_for_status(r)
        except HTTPError as e:
            raise HTTPError(
                "Invalid user token. if you did pass a user token, double-check it's correct.",
                request=e.request,
                response=e.response,
            ) from e

        data = r.json().get("data")
        if not data or not isinstance(data, dict):
            raise KeyError("response is not correct")
        account = data.get("account")
        if not account:
            raise KeyError("account is None")
        email = data.get("email")
        if not email:
            raise KeyError("email is None")
        user = {"username": account, "email": email}
        return user

    @validate_om_hub_args
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
        if revision is None:
            revision = DEFAULT_REVISION
        commit_message = commit_message or f"Upload {path_in_repo} with openMind hub"
        operation = CommitOperationAdd(
            path_or_fileobj=path_or_fileobj,
            path_in_repo=path_in_repo,
        )

        self.create_commit(
            repo_id=repo_id,
            operations=[operation],
            commit_message=commit_message,
            commit_description=commit_description,
            token=token,
            revision=revision,
        )

    @validate_om_hub_args
    def delete_file(
        self,
        path_in_repo: str,
        repo_id: str,
        *,
        token: Union[str, bool, None] = None,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
    ) -> CommitInfo:
        """
        Deletes a file in the given repo.

        Args:
            path_in_repo (`str`):
                Relative filepath in the repo.
            repo_id (`str`):
                The repository from which the file will be deleted, for example:
                `"username/custom_transformers"`
            token (`str`):
                openMind token.
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if the file is in a dataset or
                space, `None` or `"model"` if in a model. Default is `None`.
            revision (`str`, *optional*):
                The git revision to commit from. Defaults to the head of the `"main"` branch.
            commit_message (`str`, *optional*):
                The summary / title / first line of the generated commit. Defaults to
                `f"Delete {path_in_repo} with openmind"`.
            commit_description (`str` *optional*)
                The description of the generated commit.

        """
        commit_message = commit_message if commit_message is not None else f"Delete {path_in_repo} with openmind"

        operations = [CommitOperationDelete(path_in_repo=path_in_repo)]

        return self.create_commit(
            repo_id=repo_id,
            repo_type=repo_type,
            token=token,
            operations=operations,
            revision=revision,
            commit_message=commit_message,
            commit_description=commit_description,
        )

    @validate_om_hub_args
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
        """
        Creates a commit in the given repo, deleting & uploading files as needed.
        """
        if not commit_message:
            raise ValueError("`commit_message` can't be empty, please pass a value.")
        commit_description = commit_description or ""

        check_admin()

        operations = list(operations)
        additions = [op for op in operations if isinstance(op, CommitOperationAdd)]
        for addition in additions:
            if addition.is_committed:
                error_msg = (
                    f"CommitOperationAdd {addition} has "
                    f"already being committed and cannot be reused. Please create a"
                    " new CommitOperationAdd object if you want to create a new commit."
                )
                raise ValueError(replace_invalid_characters(error_msg))
        logger.debug(f"About to commit to the hub: {len(additions)} addition(s).")

        # If updating a README.md file, make sure the metadata format is valid
        # It's better to fail early than to fail after all the files have been uploaded.
        for addition in additions:
            if addition.path_in_repo == "README.md":
                with addition.as_file() as file:
                    bytes_string = file.read()
                    string_content = bytes_string.decode("utf-8")

                    normalized_string = string_content.replace("\r\n", "\n")
                    base64_bytes = base64.b64encode(normalized_string.encode("utf-8"))

                    base64_string = base64_bytes.decode("utf-8")
                    response = get_session().post(
                        f"{ENDPOINT}/api/v1/file/license_check",
                        json={"content": base64_string},
                    )
                    data = response.json().get("data")
                    if not data:
                        raise ValueError("license error, check your license in README.md please")

        _warn_on_overwriting_operations(operations)

        if not token:
            token = self.token
        self.preupload_lfs_files(
            repo_id=repo_id,
            additions=additions,
            token=token,
            num_threads=num_threads,
            free_memory=False,
            revision=revision,
        )

        commit_url = f"{self.endpoint}/api/v1/file/{repo_id}/upload"
        headers = self.build_om_headers(token=token or self.token)
        commit_payload = _prepare_commit_payload(
            operations=operations, commit_message=commit_message, revision=revision
        )
        logger.info("create_commit send HTTPS request")
        commit_resp = get_session().post(
            url=commit_url,
            json=commit_payload,
            headers=headers,
            timeout=CREATE_COMMIT_TIMEOUT,
        )
        del token, headers
        gc.collect()
        om_raise_for_status(commit_resp, endpoint_name="commit")

        # Mark additions as committed (cannot be reused in another commit)
        for addition in additions:
            addition.is_committed = True

        commit_data = commit_resp.json()
        if commit_resp.status_code > 201:
            return commit_data.get("message")

        commit_data = commit_data.get("data", [])
        commit_oid = ""

        if commit_data:
            commit_url = "; ".join(f.get("commit_url", "") for f in commit_data)
            commit_oid = "; ".join(f.get("commit_oid", "") for f in commit_data)

        return CommitInfo(
            commit_url=commit_url,
            commit_message=commit_message,
            commit_description=commit_description,
            oid=commit_oid,
        )

    def preupload_lfs_files(
        self,
        repo_id: str,
        additions: Iterable[CommitOperationAdd],
        *,
        token: Optional[str] = None,
        num_threads: int = 5,
        free_memory: bool = True,
        revision: Optional[str] = None,
        **kwargs,
    ):
        # Filter out already uploaded files
        new_additions = [addition for addition in additions if not addition.is_uploaded]

        _fetch_upload_modes(
            repo_id=repo_id,
            additions=new_additions,
            token=token or self.token,
            revision=revision,
            endpoint=self.endpoint,
        )

        new_lfs_files = [addition for addition in new_additions if addition.upload_mode == "lfs"]

        # Upload new LFS files
        _upload_lfs_files(
            additions=new_lfs_files,
            repo_id=repo_id,
            token=token or self.token,
            endpoint=self.endpoint,
            num_threads=num_threads,
        )

        del token
        gc.collect()

        for addition in new_lfs_files:
            addition.is_uploaded = True
            if free_memory:
                addition.path_or_fileobj = b""

    @validate_om_hub_args
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
        """
        Upload a local folder to the given repo. The upload is done through an HTTP request, and doesn't require git or
        git-lfs to be installed.

        Use the `ignore_patterns` argument to specify which files to upload. These parameters
        accept either a single pattern or a list of patterns. Patterns are Standard Wildcards (globbing patterns) as
        documented [here](https://tldp.org/LDP/GNU-Linux-Tools-Summary/html/x11655.htm).

        Any `.git/` folder present in any subdirectory will be ignored. However, please be aware that the `.gitignore`
        file is not taken into account.

        Args:
            repo_id (`str`):
                The repository to which the file will be uploaded, for example:
                `"username/custom_transformers"`
            folder_path (`str` or `Path`):
                Path to the folder to upload on the local file system
            path_in_repo (`str`, *optional*):
                Relative path of the directory in the repo, for example:
                `"checkpoints/1fec34a/results"`. Will default to the root folder of the repository.
            token (`str`, *optional*):
                Authentication token.
            revision (`str`, *optional*):
                Revision to upload to.
            commit_message (`str`, *optional*):
                The summary / title / first line of the generated commit. Defaults to:
                `f"Upload {path_in_repo} with openMind hub"`
            commit_description (`str` *optional*):
                The description of the generated commit
            allow_patterns (`List[str]` or `str`, *optional*):
                If provided, only files matching at least one pattern are uploaded.
            ignore_patterns (`List[str]` or `str`, *optional*):
                If provided, files matching any of the patterns are not uploaded.
            num_threads (`int` *optional*):
                The threads num

        Returns:
            `str`: A URL to visualize the uploaded folder on the hub.
        """
        if revision is None:
            revision = DEFAULT_REVISION
        commit_message = commit_message or "Upload folder using openMind hub"

        # Do not upload .git folder
        if ignore_patterns is None:
            ignore_patterns = []
        elif isinstance(ignore_patterns, str):
            ignore_patterns = [ignore_patterns]
        ignore_patterns += IGNORE_GIT_FOLDER_PATTERNS

        delete_patterns = kwargs.pop("delete_patterns", None)
        delete_operations = self._prepare_upload_folder_deletions(
            repo_id=repo_id,
            revision=revision,
            token=token,
            path_in_repo=path_in_repo,
            delete_patterns=delete_patterns,
        )

        add_operations = _prepare_upload_folder_additions(
            folder_path,
            path_in_repo,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
        )
        commit_operations = delete_operations + add_operations

        commit_inf = self.create_commit(
            repo_id=repo_id,
            operations=commit_operations,
            commit_message=commit_message,
            commit_description=commit_description,
            token=token,
            revision=revision,
            num_threads=num_threads,
        )

        del token
        gc.collect()

        return commit_inf.commit_url

    @validate_om_hub_args
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
        """Create an empty repo.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated
                by a `/`.
            token (`str`, *optional*):
                An authentication token.
            private (`bool`, *optional*, defaults to `False`):
                Whether the model repo should be private.
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if uploading to a dataset or
                space, `None` or `"model"` if uploading to a model. Default is
                `None`.
            exist_ok (`bool`, *optional*, defaults to `False`):
                If `True`, do not raise an error if repo already exists.
            desc (`str`, *optional*):
                Description of the repo.
            fullname (`str`, *optional*):
                Fullname of the repo.
            license (`str`):
                Include: apache-2.0, mit, cc-by-sa-3.0, afl-3.0, lgpl-lr, etc.
            space_sdk (`str`, *optional*):
                Choice of SDK to use if repo_type is "space". Can be "gradio" or "static".
            space_hardware (`SpaceHardware` or `str`, *optional*):
                Choice of Hardware if repo_type is "space". See [`SpaceHardware`] for a complete list.
            space_image (`str`, *optional*):
                Choice of base image to use if repo_type is "space". Can be "openeuler-python3.8-pytorch2.1.0-openmind0.7.1",
                "openeuler-python3.9-pytorch2.1.0-openmind0.8.0", "openeuler-python3.8-mindspore2.3.0rc1-openmind0.7.1",
                "openeuler-python3.9-mindspore2.3.1-openmind0.8.0".

        Returns:
            [`RepoUrl`]: URL to the newly created repo. Value is a subclass of `str` containing
            attributes like `endpoint`, `repo_type` and `repo_id`.
        """
        if repo_type not in REPO_TYPES:
            raise ValueError("Invalid repo type")

        owner, name = repo_id.split("/") if "/" in repo_id else (None, repo_id)
        if not owner:
            owner = self.whoami(token=token).get("username", None)
            if not owner:
                raise ValueError("the username not in user dict")

            repo_id = f"{owner}/{name}"
        if not repo_type:
            repo_type = REPO_TYPE_MODEL
        path = f"{self.endpoint}/api/v1/{repo_type}"

        json: Dict[str, Any] = {"name": name, "owner": owner, "license": license}
        if private:
            json["visibility"] = "private"
        else:
            json["visibility"] = "public"
        if desc:
            json["desc"] = desc
        if fullname:
            json["fullname"] = fullname
        if repo_type == "space":
            if not space_sdk or space_sdk.lower() not in SPACES_SDK_TYPES:
                raise ValueError(f"Invalid space_sdk. Please choose one of {SPACES_SDK_TYPES}.")
            json["sdk"] = space_sdk
            if not space_hardware:
                raise ValueError("Invalid space_hardware. See [`SpaceHardware`] for a complete list.")
            json["hardware"] = space_hardware
            if space_image not in SPACES_IMAGES:
                raise ValueError(f"Invalid space_images. Please choose one of {SPACES_IMAGES}.")
            json["base_image"] = space_image
        space_bool = space_sdk or space_hardware or space_image
        if space_bool and repo_type != "space":
            logger.warning(
                "Ignoring provided space_sdk, space_hardware or space_image" " because repo_type is not 'space'."
            )

        headers = self.build_om_headers(token=token, is_write_action=True)
        logger.info("create_repo send HTTPS request")
        r = get_session().post(path, headers=headers, json=json, timeout=DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        try:
            om_raise_for_status(r)
        except OmHubHTTPError:
            is_expect_status_code = r.status_code == 400 and r.json().get("code") == DUPLICATE_CREATING_CODE
            if not (is_expect_status_code and exist_ok):
                raise

        return RepoUrl(f"{self.endpoint}/{repo_type}s/{repo_id}", endpoint=self.endpoint)

    @validate_om_hub_args
    def delete_repo(
        self,
        repo_id: str,
        *,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        missing_ok: bool = False,
    ) -> None:
        """
        Delete a repo from the openMind. CAUTION: this is irreversible.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated by a `/`.
            token (`str`, *optional*):
                An authentication token (See https://modelers.cn/my/tokens).
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if delete a dataset or
                space, `None` or `"model"` if delete a model.
            missing_ok (`bool`, *optional*, defaults to `False`):
                If `True`, do not raise an error if repo does not exist.

        Raises:
            - [`~utils.RepositoryNotFoundError`]
              If the repository to delete from cannot be found and `missing_ok` is set to False (default).
        """
        if repo_type not in REPO_TYPES:
            raise ValueError("Invalid repo type")
        if not repo_type:
            repo_type = REPO_TYPE_MODEL
        try:
            repo_info_id = self.repo_info(repo_id, repo_type=repo_type, token=token).id
        except RepositoryNotFoundError:
            if not missing_ok:
                raise
            else:
                return
        path = f"{self.endpoint}/api/v1/{repo_type}/{repo_info_id}"
        headers = self.build_om_headers(token=token, is_write_action=True)
        logger.info("delete_repo send HTTPS request")
        r = get_session().delete(path, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        om_raise_for_status(r)

    @validate_om_hub_args
    def model_info(
        self,
        repo_id: str,
        *,
        revision: Optional[str] = None,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> ModelInfo:
        """
        Model can be private if you pass an acceptable token.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated
                by a `/`.
            revision (`str`, *optional*):
                The revision of the repository. Defaults to `"main"` branch.
            timeout (`float`, *optional*):
                Whether to set a timeout for the request to the Hub.
            token (`str`, *optional*):
                A valid authentication token.

        Returns:
            [`ModelInfo`]: The model repository information.
        """
        revision = quote(revision, safe="") if revision is not None else DEFAULT_REVISION
        params = {"ref": revision}
        headers = self.build_om_headers(token=token)
        path = f"{self.endpoint}/api/v1/model/{repo_id}"
        logger.info("model_info send HTTPS request")
        r = get_session().get(path, headers=headers, params=params, timeout=timeout or DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        om_raise_for_status(r)
        data = r.json().get("data")
        return ModelInfo(**data)

    @validate_om_hub_args
    def get_model_ci_info(
        self,
        repo_id: str,
        *,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
    ) -> ModelCiInfo:
        headers = self.build_om_headers(token=token)
        path = f"{self.endpoint}/api/v1/model/ci/{repo_id}"
        logger.info("get_model_ci_info send HTTPS request")
        r = get_session().get(path, headers=headers, timeout=timeout or DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        om_raise_for_status(r)
        data = r.json().get("data")
        return ModelCiInfo(**data)

    @validate_om_hub_args
    def dataset_info(
        self,
        repo_id: str,
        *,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Union[int, float] = None,
        **kwargs,
    ) -> DatasetInfo:
        """
        Get info on one specific dataset on openMind.

        Dataset can be private if you pass an acceptable token.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated
                by a `/`.
            revision (`str`, *optional*):
                The revision of the repository. Defaults to `"main"` branch.
            timeout (`float`, *optional*):
                Whether to set a timeout for the request to the Hub.
            token (`str`, *optional*):
                A valid authentication token.

        Returns:
            [`DatasetInfo`]: The dataset repository information.
        """
        revision = quote(revision, safe="") if revision is not None else DEFAULT_REVISION
        params = {"ref": revision}
        headers = self.build_om_headers(token=token)
        path = f"{self.endpoint}/api/v1/dataset/{repo_id}"

        MAX_RETRIES = 10
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                r = get_session().get(path, headers=headers, params=params, timeout=timeout or DEFAULT_REQUEST_TIMEOUT)
                om_raise_for_status(r)
                data = r.json().get("data")
                data["sha"] = self.get_repo_last_commit(repo_id=repo_id, token=token, revision=revision).oid
                return DatasetInfo(**data)
            except RepositoryNotFoundError as e:
                raise RepositoryNotFoundError(message="该数据集不存在") from e
            except Exception as e:
                retry_count += 1
                logger.info(f"Error occurred during dataset_info on attempt {retry_count}/{MAX_RETRIES}: {str(e)}. ")
                if retry_count == MAX_RETRIES:
                    raise e
                time.sleep(2)

    @validate_om_hub_args
    def space_info(
        self,
        repo_id: str,
        *,
        revision: Optional[str] = None,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> SpaceInfo:
        """
        Get info on one specific space on openMind.

        Space can be private if you pass an acceptable token.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated
                by a `/`.
            revision (`str`, *optional*):
                The revision of the repository. Defaults to `"main"` branch.
            timeout (`float`, *optional*):
                Whether to set a timeout for the request to the Hub.
            token (`str`, *optional*):
                A valid authentication token.

        Returns:
            [`SpaceInfo`]: The space repository information.
        """
        revision = quote(revision, safe="") if revision is not None else DEFAULT_REVISION
        params = {"ref": revision}
        headers = self.build_om_headers(token=token)
        path = f"{self.endpoint}/api/v1/space/{repo_id}"
        r = get_session().get(path, headers=headers, params=params, timeout=timeout or DEFAULT_REQUEST_TIMEOUT)
        om_raise_for_status(r)
        data = r.json().get("data")
        return SpaceInfo(**data)

    def list_models(
        self,
        filter: Union[ModelFilter, None] = None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> Iterable[ModelInfo]:
        path = f"{self.endpoint}/api/v1/model"
        headers = self.build_om_headers(token=token)
        params = {}
        if isinstance(filter, ModelFilter):
            if filter.author:
                if not isinstance(filter.author, str):
                    raise ValueError("The input ModelFilter is invalid.")
                params["owner"] = filter.author
            if filter.model_name:
                params["name"] = filter.model_name
            if filter.task:
                if not isinstance(filter.task, str) and not isinstance(filter.task, list):
                    raise ValueError("The input ModelFilter is invalid.")
                if isinstance(filter.task, list):
                    for task in filter.task:
                        if not isinstance(task, str):
                            raise ValueError("The input ModelFilter is invalid.")
                params["task"] = filter.task
            if filter.tags:
                if isinstance(filter.tags, list):
                    for tag in filter.tags:
                        if not isinstance(tag, str):
                            raise ValueError("The input ModelFilter is invalid.")
                params["others"] = filter.tags
            if filter.license:
                params["license"] = filter.license
            if filter.library:
                if isinstance(filter.library, list):
                    for library in filter.library:
                        if not isinstance(library, str):
                            raise ValueError("The input ModelFilter is invalid.")
                params["frameworks"] = filter.library
            if filter.sort_by:
                params["sort_by"] = filter.sort_by
            if filter.limit:
                params["count_per_page"] = filter.limit
        if author and isinstance(author, str):
            params["owner"] = author
        if limit and isinstance(limit, int):
            params["count_per_page"] = limit

        logger.info("list_models send HTTPS request")
        r = get_session().get(path, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()
        om_raise_for_status(r)
        data = r.json().get("data")

        if not data:
            raise KeyError("data is None")
        if not isinstance(data, dict):
            raise KeyError("response is not correct")
        model_list = data.get("models")
        if not model_list:
            model_list = []
        for model in model_list:
            yield ModelInfo(**model)

    def list_datasets(
        self,
        filter: Union[DatasetFilter, None] = None,
        author: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[DatasetInfo]:
        """
        List datasets hosted on the openMind Hub, given some filters.

        Args:
            filter ([`DatasetFilter`] or `str` or `Iterable`, *optional*):
                A string or [`DatasetFilter`] which can be used to identify
                datasets on the hub.
            author (`str`, *optional*):
                A string which identify the author of the returned datasets.
            full (`bool`, *optional*):
                Whether to fetch all dataset data, including the `last_modified`,
                the `card_data` and  the files. Can contain useful information such as the
                PapersWithCode ID.
            token (`str`, *optional*):
                A valid authentication token.

        Returns:
            `Iterable[DatasetInfo]`: an iterable of [`.om_api.DatasetInfo`] objects.
        """
        path = f"{self.endpoint}/api/v1/dataset"
        headers = self.build_om_headers(token=token)
        params = {}

        if author:
            params.update({"owner": author})
        params.update(**kwargs)

        r = get_session().get(path, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        om_raise_for_status(r)
        data = r.json().get("data")
        if data is None:
            raise KeyError("data is None")
        dataset_list = data.get("datasets")
        if dataset_list is not None:
            for dataset in dataset_list:
                yield DatasetInfo(**dataset)

    def list_metrics(self) -> List[MetricInfo]:
        """
        Get the public list of all the metrics on openMind.

        Returns:
            `List[MetricInfo]`: a list of [`MetricInfo`] objects which.
        """
        return []

    def list_spaces(
        self,
        author: Optional[str] = None,
        space_name: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[SpaceInfo]:
        """
        query space list
        """
        path = f"{self.endpoint}/api/v1/space"
        headers = self.build_om_headers(token=token)
        params = {}
        if author:
            params["owner"] = author
        if space_name:
            params["name"] = space_name
        if sort:
            params["sort_by"] = sort
        if limit:
            params["count_per_page"] = limit

        r = get_session().get(path, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        om_raise_for_status(r)
        data = r.json().get("data")
        if data is None:
            raise KeyError("data is None")
        space_list = data["spaces"]
        if not space_list:
            space_list = []
        for space in space_list:
            yield SpaceInfo(**space)

    @validate_om_hub_args
    def restart_space(self, repo_id: str, token: Optional[str] = None, **kwargs):
        """Restart your Space.

        This is the only way to programmatically restart a Space if you've put it on Pause (see [`pause_space`]). You
        must be the owner of the Space to restart it. If you are using an upgraded hardware, your account will be
        billed as soon as the Space is restarted. You can trigger a restart no matter the current state of a Space.

        Args:
            repo_id (`str`):
                ID of the Space to restart. Example: `"Salesforce/BLIP2"`.
            token (`str`, *optional*):
                openMind token. Will default to the locally saved token if not provided.

        Raises:
            [`~utils.RepositoryNotFoundError`]:
                If your Space is not found (error 404). Most probably wrong repo_id or your space is private, but you
                are not authenticated.
            [`~utils.OmHubHTTPError`]:
                401 Forbidden: only the owner of a Space can restart it. If you want to restart a Space that you don't
                own, either ask the owner by opening a Discussion or duplicate the Space.
            [`~utils.BadRequestError`]:
                If your Space is a static Space. Static Spaces are always running and never billed. If you want to hide
                a static Space, you can set it to private.
        """
        r = get_session().post(
            f"{self.endpoint}/api/v1/space-app/{repo_id}/restart",
            headers=self.build_om_headers(token=token),
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        om_raise_for_status(r)

    @validate_om_hub_args
    def repo_info(
        self,
        repo_id: str,
        *,
        revision: Optional[str] = None,
        repo_type: Optional[str] = None,
        timeout: Union[int, float] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Union[ModelInfo, DatasetInfo, SpaceInfo]:
        if not repo_type or repo_type == REPO_TYPE_MODEL:
            method = self.model_info
        elif repo_type == "dataset":
            method = self.dataset_info
        elif repo_type == "space":
            method = self.space_info
        else:
            raise ValueError("Unsupported repo type.")
        return method(
            repo_id,
            token=token,
            timeout=timeout,
            revision=revision,
        )

    @validate_om_hub_args
    def list_repo_tree(
        self,
        repo_id: str,
        path_in_repo: Optional[str] = None,
        *,
        recursive: bool = False,
        revision: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Iterable[Union[RepoFile, RepoFolder]]:
        """
        List a repo tree's files and folders and get information about them.

        Args:
            repo_id (`str`):
                A namespace (user or an organization) and a repo name separated by a `/`.
            path_in_repo (`str`, *optional*):
                Relative path of the tree (folder) in the repo. Will default to the root tree of the repository.
            revision (`str`, *optional*):
                The revision of the repository from which to get the tree. Defaults to `"main"` branch.
            token (`str`, *optional*):
                An authentication token (See https://modelers.cn/my/tokens).

        Returns:
            `Iterable[Union[RepoFile, RepoFolder]]`:
                The information about the tree's files and folders, as an iterable of [`RepoFile`] and
                [`RepoFolder`] objects.

        Raises:
            [`~utils.RepositoryNotFoundError`]:
                If repository is not found (error 404): wrong repo_id/repo_type, private but not authenticated or repo
                does not exist.
            [`~utils.RevisionNotFoundError`]:
                If revision is not found (error 404) on the repo.
            [`~utils.EntryNotFoundError`]:
                If the tree (folder) does not exist (error 404) on the repo.

        Examples:

            Get information about a repo's tree.
            ```py
            >>> from openmind_hub import list_repo_tree
            >>> repo_tree = list_repo_tree("lysandre/arxiv-nlp")
            >>> repo_tree
            <generator object OmApi.list_repo_tree at 0x7fa4088e1ac0>
            ```
        """
        revision = quote(revision, safe="") if revision is not None else DEFAULT_REVISION
        headers = self.build_om_headers(token=token)
        params = {}
        if path_in_repo is not None:
            params["path"] = path_in_repo
        else:
            params["path"] = ""
        if revision is not None:
            params["ref"] = revision

        url = f"{self.endpoint}/api/v1/file/{repo_id}"
        r = get_session().get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        om_raise_for_status(r)
        data = r.json().get("data")
        if data is None:
            raise KeyError("data is None")
        file_tree = data.get("tree")
        if file_tree is None:
            raise KeyError("file_tree is None")
        all_path = set()
        if recursive:
            for info in file_tree:
                info_type = info.get("type")
                path = info.get("path")
                if path in all_path:
                    continue
                if info_type == "dir":
                    all_path.add(path)
                    params["path"] = path
                    session_data = (
                        get_session()
                        .get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
                        .json()
                        .get("data")
                    )
                    if session_data is None:
                        raise KeyError("session_data is None")
                    tmp_list = session_data.get("tree")
                    file_tree.extend(tmp_list)
        for info in file_tree:
            yield RepoFile(**info) if info.get("type") == "file" else RepoFolder(**info)

    def list_repo_files(
        self,
        repo_id: str,
        *,
        revision: Optional[str] = None,
        token: Union[str, bool, None] = None,
        **kwargs,
    ) -> List[str]:
        """
        Get the list of files in a given repo.

        Returns:
            `List[str]`: the list of files in a given repository.
        """
        return [
            f.path
            for f in self.list_repo_tree(repo_id=repo_id, revision=revision, token=token, recursive=True)
            if isinstance(f, RepoFile)
        ]

    @validate_om_hub_args
    def get_repo_last_commit(
        self,
        repo_id: str,
        path_in_repo: Optional[str] = None,
        *,
        revision: Optional[str] = None,
        token: Optional[str] = None,
    ) -> LastCommitInfo:
        revision = quote(revision, safe="") if revision is not None else DEFAULT_REVISION
        headers = self.build_om_headers(token=token)
        params = {}
        if revision is not None:
            params["ref"] = revision
        if path_in_repo is not None:
            params["path"] = path_in_repo
        else:
            params["path"] = ""
        url = f"{self.endpoint}/api/v1/file/{repo_id}"
        r = get_session().get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        om_raise_for_status(r)
        data = r.json().get("data")
        if data is None:
            raise KeyError("data is None")
        last_commit = data.get("last_commit", {}).get("commit", {})
        update_at = last_commit.get("created", "")
        if update_at.endswith("Z"):
            update_at = datetime.fromisoformat(update_at[:-1])
        elif update_at.endswith("+08:00"):
            update_at = datetime.fromisoformat(update_at[:-6])
        else:
            update_at = datetime.fromisoformat(update_at)
        commit_info = LastCommitInfo(
            oid=last_commit.get("commit_sha"), title=last_commit.get("message"), date=update_at
        )
        return commit_info

    @validate_om_hub_args
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
        """
        Create a new branch for a repo on the Hub, starting from the specified revision (defaults to `main`).

        Args:
            repo_id (`str`):
                The repository in which the branch will be created.
                Example: `"user/my-cool-model"`.
            branch (`str`):
                The name of the branch to create.
            revision (`str`, *optional*):
                The git revision to create the branch from. It can be a branch name or
                the OID/SHA of a commit, as a hexadecimal string. Defaults to the head
                of the `"main"` branch.
            token (`str`, *optional*):
                Authentication token. Will default to the stored token.
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if creating a branch on a dataset or
                space, `None` or `"model"` if tagging a model. Default is `None`.
            exist_ok (`bool`, *optional*, defaults to `False`):
                If `True`, do not raise an error if branch already exists.

        Raises:
            [`~utils.RepositoryNotFoundError`]:
                If repository is not found (error 404): wrong repo_id/repo_type, private
                but not authenticated or repo does not exist.
            [`~utils.BadRequestError`]:
                If invalid reference for a branch. Ex: `refs/pr/5` or 'refs/foo/bar'.
            [`~utils.OmHubHTTPError`]:
                If the branch already exists on the repo (error 400) and `exist_ok` is
                set to `False`.
        """
        repo_type = repo_type or REPO_TYPE_MODEL
        if repo_type not in REPO_TYPES:
            raise ValueError("Invalid repo type")
        if revision is None:
            revision = DEFAULT_REVISION

        path = f"{self.endpoint}/api/v1/branch/{repo_type}/{repo_id}"
        headers = self.build_om_headers(token=token, is_write_action=True)
        json = {"branch": branch, "base_branch": revision}

        logger.info("create_branch send HTTPS request")
        response = get_session().post(path, headers=headers, json=json, timeout=DEFAULT_REQUEST_TIMEOUT)
        del token, headers
        gc.collect()

        try:
            om_raise_for_status(response)
        except OmHubHTTPError:
            if not (response.status_code == 400 and exist_ok):
                raise

    @validate_om_hub_args
    def delete_branch(
        self,
        repo_id: str,
        *,
        branch: str,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
    ) -> None:
        """
        Delete a branch from a repo on the Hub.

        Args:
            repo_id (`str`):
                The repository in which a branch will be deleted.
                Example: `"user/my-cool-model"`.
            branch (`str`):
                The name of the branch to delete.
            token (`str`, *optional*):
                Authentication token. Will default to the stored token.
            repo_type (`str`, *optional*):
                Set to `"dataset"` or `"space"` if deleting a branch on a dataset or
                space, `None` or `"model"` if tagging a model. Default is `None`.

        Raises:
            [`~utils.RepositoryNotFoundError`]:
                If repository is not found (error 404): wrong repo_id/repo_type, private
                but not authenticated or repo does not exist.
            [`~utils.OmHubHTTPError`]:
                If trying to delete a protected branch. Ex: `main` cannot be deleted.

        """
        if not repo_type:
            repo_type = REPO_TYPE_MODEL
        if repo_type not in REPO_TYPES:
            raise ValueError("Invalid repo type")
        branch = quote(branch, safe="")

        # Prepare request
        path = f"{self.endpoint}/api/v1/branch/{repo_type}/{repo_id}/{branch}"
        headers = self.build_om_headers(token=token, is_write_action=True)

        # Delete branch
        logger.info("delete_branch send HTTPS request")
        response = get_session().delete(url=path, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)

        del token, headers
        gc.collect()

        om_raise_for_status(response)

    def get_full_repo_name(
        self,
        model_id: str,
        *,
        organization: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Returns the repository name for a given model ID and optional
        organization.

        Args:
            model_id (`str`):
                The name of the model.
            organization (`str`, *optional*):
                If passed, the repository name will be in the organization
                namespace instead of the user namespace.
            token (`str`, *optional*):
                A valid authentication token (see https://modelers.cn/my/tokens).
                If `None` or `True`, token will be retrieved from the cache.
                If `False`, token is not sent in the request header.

        Returns:
            `str`: The repository name in the user's namespace
            ({username}/{model_id}) if no organization is passed, and under the
            organization namespace ({organization}/{model_id}) otherwise.
        """
        if organization is None:
            if "/" in model_id:
                return model_id
            else:
                username = self.whoami(token=token).get("username", None)  # type: ignore
                if username is None:
                    raise ValueError("username not in user dict")
            return f"{username}/{model_id}"
        else:
            model_name = model_id.split("/")[-1]
            return f"{organization}/{model_name}"

    def get_path_info(
        self,
        repo_id: str,
        path_in_repo: str,
        *,
        revision: Optional[str] = None,
        token: Optional[str] = None,
    ) -> [Union[RepoFile, RepoFolder]]:
        params = {"ref": revision or DEFAULT_REVISION, "path": path_in_repo}
        file_url = f"{self.endpoint}/api/v1/file/{repo_id}/info?{urlencode(params)}"
        headers = self.build_om_headers(token=token)

        logger.info("get_path_info send HTTPS request")
        r = get_session().get(
            file_url,
            timeout=DEFAULT_REQUEST_TIMEOUT,
            headers=headers,
        )
        try:
            om_raise_for_status(r)
        except RepositoryNotFoundError as e:
            if e.server_message == NOT_FILE_CODE:
                last_commit = self.get_repo_last_commit(
                    repo_id,
                    token=token,
                    revision=revision,
                    path_in_repo=path_in_repo,
                )
                repo_folder = RepoFolder(path=path_in_repo)
                repo_folder.last_commit = last_commit
                return repo_folder
            else:
                raise
        except Exception:
            raise
        else:
            response_data = r.json().get("data")
            return RepoFile(**response_data)

    @validate_om_hub_args
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
        local_dir_use_symlinks: Union[bool, Literal["auto"]] = "auto",
        force_download: bool = False,
        force_filename: Optional[str] = None,
        proxies: Optional[Dict] = None,
        resume_download: bool = True,
        token: Optional[Union[str, bool]] = None,
        local_files_only: bool = False,
        legacy_cache_layout: bool = False,
    ) -> str:
        """Download a given file if it's not already present in the local cache."""
        from .file_download import om_hub_download

        token = token or self.token

        return om_hub_download(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            repo_type=repo_type,
            revision=revision,
            endpoint=self.endpoint,
            library_name=self.library_name,
            library_version=self.library_version,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_dir_use_symlinks=local_dir_use_symlinks,
            user_agent=self.user_agent,
            force_download=force_download,
            force_filename=force_filename,
            proxies=proxies,
            resume_download=resume_download,
            token=token,
            local_files_only=local_files_only,
        )

    @validate_om_hub_args
    def snapshot_download(
        self,
        repo_id: str,
        *,
        repo_type: Optional[str] = None,
        revision: Optional[str] = None,
        cache_dir: Union[str, Path, None] = None,
        local_dir: Union[str, Path, None] = None,
        local_dir_use_symlinks: Union[bool, Literal["auto"]] = "auto",
        proxies: Optional[Dict] = None,
        resume_download: bool = True,
        force_download: bool = False,
        token: Optional[str] = None,
        local_files_only: bool = False,
        allow_patterns: Optional[Union[List[str], str]] = None,
        ignore_patterns: Optional[Union[List[str], str]] = None,
        max_workers: int = 8,
        tqdm_class: Optional[base_tqdm] = None,
    ) -> str:
        from ._snapshot_download import snapshot_download

        token = token or self.token

        return snapshot_download(
            repo_id=repo_id,
            repo_type=repo_type,
            revision=revision,
            endpoint=self.endpoint,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_dir_use_symlinks=local_dir_use_symlinks,
            library_name=self.library_name,
            library_version=self.library_version,
            user_agent=self.user_agent,
            proxies=proxies,
            resume_download=resume_download,
            force_download=force_download,
            token=token,
            local_files_only=local_files_only,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            max_workers=max_workers,
            tqdm_class=tqdm_class,
        )

    def build_om_headers(
        self,
        token: Optional[str] = None,
        is_write_action: bool = False,
        library_name: Optional[str] = None,
        library_version: Optional[str] = None,
        user_agent: Union[Dict, str, None] = None,
    ) -> Dict[str, str]:
        """
        Alias for [`build_om_headers`] that uses the token from [`OmApi`] client
        when `token` is not provided.
        """
        if not token:
            token = self.token
        return build_om_headers(
            token=token,
            is_write_action=is_write_action,
            library_name=library_name or self.library_name,
            library_version=library_version or self.library_version,
            user_agent=user_agent or self.user_agent,
        )

    def _prepare_upload_folder_deletions(
        self,
        repo_id: str,
        revision: Optional[str],
        path_in_repo: str,
        delete_patterns: Optional[Union[List[str], str]],
        token: Union[bool, str, None] = None,
    ) -> List[CommitOperationDelete]:
        """Generate the list of Delete operations for a commit to delete files from a repo.

        List remote files and match them against the `delete_patterns` constraints. Returns a list
        of [`CommitOperationDelete`] with the matching items.

        Note: `.gitattributes` file is essential to make a repo work properly on the Hub. This file will always be
              kept even if it matches the `delete_patterns` constraints.
        """
        if delete_patterns is None:
            # If no delete patterns, no need to list and filter remote files
            return []

        # List remote files
        filenames = self.list_repo_files(repo_id=repo_id, revision=revision, token=token)

        # Compute relative path in repo
        if path_in_repo and path_in_repo not in (".", "./"):
            path_in_repo = path_in_repo.strip("/") + "/"  # harmonize
            relpath_to_abspath = {
                file[len(path_in_repo) :]: file for file in filenames if file.startswith(path_in_repo)
            }
        else:
            relpath_to_abspath = {file: file for file in filenames}

        # Apply filter on relative paths and return
        return [
            CommitOperationDelete(path_in_repo=relpath_to_abspath[relpath], is_folder=False)
            for relpath in filter_repo_objects(relpath_to_abspath.keys(), allow_patterns=delete_patterns)
            if relpath_to_abspath[relpath] != ".gitattributes"
        ]


if os.getenv("OPENMIND_PLATFORM") == "gitcode":
    api = OmApi(endpoint=ENDPOINT)
else:
    api = OmApi()

whoami = api.whoami

upload_file = api.upload_file
upload_folder = api.upload_folder
create_commit = api.create_commit

list_repo_tree = api.list_repo_tree
snapshot_download = api.snapshot_download

create_repo = api.create_repo
delete_repo = api.delete_repo

create_branch = api.create_branch
delete_branch = api.delete_branch

repo_info = api.repo_info
model_info = api.model_info
list_models = api.list_models
get_model_ci_info = api.get_model_ci_info

dataset_info = api.dataset_info
list_datasets = api.list_datasets
list_metrics = api.list_metrics

space_info = api.space_info
list_spaces = api.list_spaces
restart_space = api.restart_space

get_full_repo_name = api.get_full_repo_name
