# Copyright 2022-present, the HuggingFace Inc. team.
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
import os
from functools import wraps
import inspect
from itertools import chain
import re
from pathlib import Path
from typing import Callable, TypeVar
from urllib.parse import urlparse

from ..constants import (
    OM_HOME,
    SENSITIVE_PATHS,
    WHITE_LIST_PATHS,
    HOSTNAME_WHITE_LIST,
    UPLOAD_OBS_HOSTNAME_WHITE_LIST,
    DOWNLOAD_CDN_HOSTNAME_WHITE_LIST,
)
from ._error import OMValidationError
from .logging import replace_invalid_characters

CallableT = TypeVar("CallableT", bound=Callable)

OWNER_NAME_REGEXP = re.compile("^[a-zA-Z]([-_.%]([a-zA-Z0-9])|[a-zA-Z0-9]){2,39}$")
REPO_NAME_REGEXP = re.compile("^[a-zA-Z0-9._-]{1,100}$")
BRANCH_REGEXP = re.compile("^[a-zA-Z0-9_-]{1,100}$")
REVISION_REGEXP = re.compile("^[a-zA-Z0-9]+$")


def validate_om_hub_args(func: CallableT) -> CallableT:
    """Validate values received as argument for any public method of `openmind`.

    Validators:
        - [`~utils.validate_repo_id`]: `repo_id` must be `"repo_name"`
          or `"namespace/repo_name"`. Namespace is a username or an organization.
    ```

    Raises:
        [`~utils.OMValidationError`]:
            If an input is not valid.
    """
    signature = inspect.signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        for arg_name, arg_value in chain(
            zip(signature.parameters, args),
            kwargs.items(),
        ):
            if arg_name == "repo_id":
                if arg_value.count("/") == 2:
                    arg_value = validate_gitcode_repo_id(arg_value)
                    kwargs[arg_name] = arg_value
                else:
                    validate_repo_id(arg_value)
            if arg_name == "branch":
                validate_branch(arg_value)
            if arg_name == "revision":
                validate_revision(arg_value)
            if arg_name == "endpoint":
                validate_url(arg_value)
            if arg_name == "url":
                validate_url(arg_value)

        return func(*args, **kwargs)

    return wrapper


def validate_repo_id(repo_id: str) -> None:
    if isinstance(repo_id, str):
        if repo_id.count("/") > 1:
            raise OMValidationError("Repo id must be in the form 'repo_name' or 'owner/repo_name'")
        owner, repo = repo_id.split("/") if "/" in repo_id else (None, repo_id)
        if owner is not None and not OWNER_NAME_REGEXP.match(owner):
            raise OMValidationError("invalid owner name")
        if repo.endswith(".git"):
            raise OMValidationError("repo name cannot end by '.git'")
        if repo is not None and not REPO_NAME_REGEXP.match(repo):
            raise OMValidationError("invalid repo name")
    else:
        raise OMValidationError("repo_id type must be string")


def validate_gitcode_repo_id(repo_id: str) -> str:
    if not isinstance(repo_id, str):
        raise OMValidationError("repo_id type must be string")
    if os.getenv("OPENMIND_PLATFORM") != "gitcode":
        raise OMValidationError("Repo id must be in the form 'repo_name' or 'owner/repo_name'")

    repo_id = repo_id[: repo_id.find("/")] + "%2F" + repo_id[repo_id.find("/") + 1 :]

    owner, repo = repo_id.split("/") if "/" in repo_id else (None, repo_id)

    if repo.endswith(".git"):
        raise OMValidationError("repo name cannot end by '.git'")
    if repo is not None and not REPO_NAME_REGEXP.match(repo):
        raise OMValidationError("invalid repo name")

    return repo_id


def validate_branch(branch: str) -> None:
    if isinstance(branch, str):
        if not BRANCH_REGEXP.match(branch):
            raise OMValidationError("invalid branch")
    else:
        if branch is None:
            return
        raise OMValidationError("branch type must be string")


def validate_revision(revision: str) -> None:
    if isinstance(revision, str):
        if not BRANCH_REGEXP.match(revision) and not REVISION_REGEXP.match(revision):
            raise OMValidationError("invalid revision")
    else:
        if revision is None:
            return
        raise OMValidationError("revision type must be string")


# validate_url checks input endpoint and url.
def validate_url(url: str) -> None:
    if isinstance(url, str):
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https":
            raise OMValidationError(replace_invalid_characters(f"{url} must use HTTPS"))
        for host in HOSTNAME_WHITE_LIST:
            if parsed_url.hostname.endswith(host):
                return
        raise ValueError(replace_invalid_characters(f"{url} is not within the white list."))
    else:
        if url is None:
            return
        raise OMValidationError("url type must be string")


# validate_upload_url checks the url while upload.
def validate_upload_url(url: str) -> None:
    if isinstance(url, str):
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https":
            raise OMValidationError("The upload url is not HTTPS.")
        for host in UPLOAD_OBS_HOSTNAME_WHITE_LIST:
            if parsed_url.hostname.endswith(host):
                return
        raise ValueError("The upload url is not within the white list.")
    else:
        if url is None:
            return
        raise OMValidationError("The upload url type is not string.")


# validate_download_url checks the url while download.
def validate_download_url(url: str) -> None:
    if isinstance(url, str):
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https":
            raise OMValidationError(replace_invalid_characters(f"Download url: {url} is not HTTPS."))
        for host in DOWNLOAD_CDN_HOSTNAME_WHITE_LIST:
            if parsed_url.hostname.endswith(host):
                return
        raise ValueError(replace_invalid_characters(f"Download url: {url} is not within the white list."))
    else:
        if url is None:
            return
        raise OMValidationError("Download url type is not string.")


def is_sensitive_path(local_dir_filepath: str):
    if isinstance(local_dir_filepath, Path):
        local_dir_filepath = str(local_dir_filepath)
    local_dir_filepath = local_dir_filepath.lstrip("\\\\?\\")
    # this function check the dir sensitive.
    path_to_check = os.path.abspath(local_dir_filepath)

    def black_white_path(path):
        if path.startswith(OM_HOME):
            return
        for sensitive_path in SENSITIVE_PATHS:
            if path.startswith(sensitive_path):
                error_msg = f"Access denied: {path} is within `constants.SENSITIVE_PATHS`"
                raise ValueError(replace_invalid_characters(error_msg))
        for white_list_path in WHITE_LIST_PATHS:
            if path.startswith(os.path.abspath(white_list_path)):
                return
        raise ValueError(
            replace_invalid_characters(
                f"Access denied: {path} is not within `constants.WHITE_LIST_PATHS`."
                "Consider set the `HUB_WHITE_LIST_PATHS` environment."
            )
        )

    black_white_path(path_to_check)
    if os.path.islink(path_to_check):
        black_white_path(os.path.realpath(path_to_check))
