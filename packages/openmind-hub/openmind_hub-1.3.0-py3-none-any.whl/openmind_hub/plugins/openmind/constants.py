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
import functools
import hashlib
import json
import os
import re
import sys
from typing import Literal, Optional
from urllib.parse import urlparse


file_path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(file_path, "public_address_lib.json"), encoding="utf-8") as cfg_file:
    json_file = cfg_file.read()
    OPENMIND_URL = json.loads(json_file)["endpoint_url"]
    OPENMIND_TOKEN_URL = json.loads(json_file)["token_url"]
    GIT_LFS_SPE = json.loads(json_file)["git_lfs_spe"]


ENV_VARS_TRUE_VALUES = {"1", "ON", "YES", "TRUE"}


def _is_true(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.upper() in ENV_VARS_TRUE_VALUES


default_home = os.path.join(os.path.expanduser("~"), ".cache")
OM_HOME = os.path.join(os.getenv("XDG_CACHE_HOME", default_home), "openmind")
default_cache_path = os.path.join(OM_HOME, "hub")
OM_HUB_CACHE = default_cache_path

EMPTY = ""
DEFAULT_REVISION = "main"
HOSTNAME_WHITE_LIST = ["openmind.cn", "osinfra.cn", "modelers.cn", "gitcode.com", "gitcode.net", "mindspore.cn"]
UPLOAD_OBS_HOSTNAME_WHITE_LIST = [
    "openmind.cn",
    "osinfra.cn",
    "modelers.cn",
    "myhuaweicloud.com",
    "gitcode.com",
    "gitcode.net",
    "mindspore.cn",
]
DOWNLOAD_CDN_HOSTNAME_WHITE_LIST = [
    "openmind.cn",
    "osinfra.cn",
    "modelers.cn",
    "gitcode.com",
    "gitcode.net",
    "mindspore.cn",
]
ENDPOINT = os.getenv("OPENMIND_HUB_ENDPOINT", OPENMIND_URL)
if os.getenv("OPENMIND_PLATFORM") == "gitcode":
    ENDPOINT = "https://api.gitcode.com"
if urlparse(ENDPOINT).scheme != "https":
    raise ValueError("Insecure scheme detected, exiting.")

DEFAULT_ETAG_TIMEOUT = 10
DEFAULT_DOWNLOAD_TIMEOUT = 60
CREATE_COMMIT_TIMEOUT = 300
HUB_GIT_PUSH_TIMEOUT = int(os.getenv("HUB_GIT_PUSH_TIMEOUT", 3600))
# Used to override the get request timeout on a system level
DEFAULT_REQUEST_TIMEOUT: int = int(os.getenv("DEFAULT_REQUEST_TIMEOUT", DEFAULT_DOWNLOAD_TIMEOUT))
HttpMethodList = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
OM_HUB_DISABLE_SYMLINKS_WARNING: bool = False

REGEX_COMMIT_HASH = re.compile(r"^[0-9a-f]{40}$")
LFS_REGEX_COMMIT_HASH = re.compile(r"^[0-9a-f]{64}$")
REGEX_COMMIT_OID = re.compile(r"[A-Fa-f0-9]{5,40}")

BIG_FILE_SIZE = 5 * 1024 * 1024
MAX_LFS_SIZE = 128849018880
DOWNLOAD_CHUNK_SIZE = 10 * 1024 * 1024
MULTIUPLOAD_SIZE = 20000000
ONE_MEGABYTE = 1024 * 1024
MAX_RESPONSE_SIZE = 10 * 1024 * 1024

REPO_ID_SEPARATOR = "--"

# error code:
REVISION_NOT_FOUND = 404
ENTRY_NOT_FOUND = 404
GATE_REPOSITORY = 401
VALIDATION_FIELD = 1004
REPOSITORY_NOT_FOUND = 404
NOT_ON_WHITE_LIST = 418
NOT_DIR_CODE = "not_dir"
NOT_FILE_CODE = "not_file"
REF_NOT_EXIST_CODE = "ref_not_exist"
DUPLICATE_CREATING_CODE = "duplicate_creating"
BRANCH_OR_PATH_NOT_FOUND_CODE = "branch_or_path_not_found"

IGNORE_GIT_FOLDER_PATTERNS = [".git", ".git/*", "*/.git", "**/.git/**", ".gitattributes"]

REPO_TYPE_MODEL = "model"
REPO_TYPE_DATASET = "dataset"
REPO_TYPE_SPACE = "space"
REPO_TYPES = [None, REPO_TYPE_MODEL, REPO_TYPE_DATASET, REPO_TYPE_SPACE]
SPACES_SDK_TYPES = ["gradio", "static"]
SPACES_IMAGES = [
    "openeuler-python3.8-pytorch2.1.0-openmind0.7.1",
    "openeuler-python3.9-pytorch2.1.0-openmind0.8.0",
    "openeuler-python3.8-mindspore2.3.0rc1-openmind0.7.1",
    "openeuler-python3.9-mindspore2.3.1-openmind0.8.0",
]
REPO_TYPES_URL_PREFIXES = {
    REPO_TYPE_MODEL: "models/",
    REPO_TYPE_DATASET: "datasets/",
    REPO_TYPE_SPACE: "spaces/",
}
REPO_TYPES_MAPPING = {
    "datasets": REPO_TYPE_DATASET,
    "spaces": REPO_TYPE_SPACE,
    "models": REPO_TYPE_MODEL,
}

__OM_HUB_DISABLE_PROGRESS_BARS = os.environ.get("OM_HUB_DISABLE_PROGRESS_BARS")
OM_HUB_DISABLE_PROGRESS_BARS: Optional[bool] = (
    _is_true(__OM_HUB_DISABLE_PROGRESS_BARS) if __OM_HUB_DISABLE_PROGRESS_BARS is not None else None
)

# 发送HTTP请求使用的安全密码算法
CUSTOM_CIPHERS = [
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-RSA-CHACHA20-POLY1305-SHA256",
]

SENSITIVE_PATHS = ["/etc", "/var", "/bin", "/boot", "/lib", os.path.join(os.path.expanduser("~"), ".")]

for sensitive_path in SENSITIVE_PATHS[:-1]:
    if OM_HOME.startswith(os.path.normpath(os.path.abspath(sensitive_path))):
        raise ValueError(
            "Access denied: Path is within a restricted sensitive area."
            "Consider modifying the SENSITIVE_PATHS in constant.py"
        )

if os.name == "nt":
    WHITE_LIST_PATHS = [os.path.expanduser("~"), "D:/", "E:/", "F:/"]
else:
    WHITE_LIST_PATHS = ["/tmp", os.path.expanduser("~")]
white_list_paths_env = os.getenv("HUB_WHITE_LIST_PATHS")
if white_list_paths_env:
    WHITE_LIST_PATHS.extend(white_list_paths_env.split(","))

FILE_MODE = [["6", "4", "2", "0"], ["4", "0"], ["0"]]
DIR_MODE = [[], ["5", "4", "1", "0"], ["0"]]

_kwargs = {"usedforsecurity": False} if sys.version_info >= (3, 9) else {}
sha1 = functools.partial(hashlib.sha1, **_kwargs)
sha256 = functools.partial(hashlib.sha256, **_kwargs)
