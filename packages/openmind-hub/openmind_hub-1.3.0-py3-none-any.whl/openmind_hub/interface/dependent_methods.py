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
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Union, Optional, List, Any

DEFAULT_REQUEST_TIMEOUT = 60
_CACHED_NO_EXIST_T = Any
ENDPOINT = os.getenv("OPENMIND_HUB_ENDPOINT", "https://xxx")


@dataclass
class CommitInfo:
    commit_url: str
    commit_message: str
    commit_description: str
    oid: str


@dataclass(frozen=True)
class OmFileMetadata:
    commit_hash: Optional[str]
    etag: Optional[str]
    location: str
    size: Optional[int]


class SpaceHardware(str, Enum):
    CPU = "CPU basic 2 vCPU · 16GB · FREE"
    NPU = "NPU basic 16 vCPU · 128GB · FREE"


@dataclass
class RepoSibling:
    rfilename: str
    size: Optional[int] = None
    blob_id: Optional[str] = None


@dataclass
class SpaceInfo:
    id: str
    name: str
    owner: str
    fullname: str
    private: Optional[Union[bool, None]]
    library_name: Optional[str]
    tags: List[str]
    pipeline_tag: Optional[str]


@dataclass
class BlobLfsInfo(dict):
    size: int
    sha256: str

    def __post_init__(self):
        self.update(asdict(self))


@dataclass
class LastCommitInfo(dict):
    oid: str
    title: str
    date: datetime

    def __post_init__(self):
        self.update(asdict(self))


def repo_type_and_id_from_om_id(om_id: str, hub_url: Optional[str] = None):
    """return repo_type, namespace, repo_name"""
    return "repo_type", "namespace", "repo_name"
