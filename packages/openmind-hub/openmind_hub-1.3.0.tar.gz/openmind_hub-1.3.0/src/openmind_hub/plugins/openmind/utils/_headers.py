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
"""Contains utilities to handle headers to send in calls to openMind."""
import gc
import sys
from typing import Dict, Optional, Union

from ..constants import OPENMIND_TOKEN_URL
from ._validators import validate_om_hub_args

_PY_VERSION: str = sys.version.split()[0].rstrip("+")


@validate_om_hub_args
def build_om_headers(
    *,
    token: Optional[str] = None,
    is_write_action: bool = False,
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Union[Dict, str, None] = None,
) -> Dict[str, str]:
    """
    Build headers dictionary to send in a openMind call.

    By default, authorization token is always provided either from argument (explicit
    use) or retrieved from the cache (implicit use). To explicitly avoid sending the
    token to the Hub, set `token=False` or set the `OM_HUB_DISABLE_IMPLICIT_TOKEN`
    environment variable.

    In case of an API call that requires write access, an error is thrown if token is `None`.

    Args:
        token (`str`, *optional*):
            The token to be sent in authorization header for the Hub call:
                - if a string, it is used as the openMind token.
        is_write_action (`bool`, default to `False`):
            Set to True if the API call requires a write access. If `True`, the token
            will be validated (cannot be `None`).
        library_name (`str`, *optional*):
            The name of the library that is making the HTTP request. Will be added to
            the user-agent header.
        library_version (`str`, *optional*):
            The version of the library that is making the HTTP request. Will be added
            to the user-agent header.
        user_agent (`str`, `dict`, *optional*):
            The user agent info in the form of a dictionary or a single string.

    Returns:
        A `Dict` of headers to pass in your API call.

    Raises:
        [`ValueError`]
            If token is passed and "write" access is required.
        [`ValueError`]
            If "write" access is required but token is not passed.
    """
    # Get auth token to send
    _validate_token_to_send(token, is_write_action=is_write_action)

    # Combine headers
    headers = {
        "user-agent": _http_user_agent(
            library_name=library_name,
            library_version=library_version,
            user_agent=user_agent,
        )
    }
    if token:
        headers["authorization"] = f"Bearer {token}"

    del token
    gc.collect()

    return headers


def _validate_token_to_send(token: Optional[str], is_write_action: bool) -> None:
    if is_write_action:
        if not token:
            raise ValueError(
                f"Token is required (write-access action) but no token found. You need"
                f" to provide a token. See {OPENMIND_TOKEN_URL}"
            )


def _http_user_agent(
    *,
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Union[Dict, str, None] = None,
) -> str:
    """Format a user-agent string containing information about the installed packages.

    Args:
        library_name (`str`, *optional*):
            The name of the library that is making the HTTP request.
        library_version (`str`, *optional*):
            The version of the library that is making the HTTP request.
        user_agent (`str`, `dict`, *optional*):
            The user agent info in the form of a dictionary or a single string.

    Returns:
        The formatted user-agent string.
    """
    if library_name:
        ua = f"{library_name}/{library_version}"
    else:
        ua = "unknown/None"
    ua += f"; python/{_PY_VERSION}"

    if isinstance(user_agent, dict):
        ua += "; " + "; ".join(f"{k}/{v}" for k, v in user_agent.items())
    elif isinstance(user_agent, str):
        ua += "; " + user_agent

    return _deduplicate_user_agent(ua)


def _deduplicate_user_agent(user_agent: str) -> str:
    """Deduplicate redundant information in the generated user-agent."""
    # Split around ";" > Strip whitespaces > Store as dict keys (ensure unicity) >
    # format back as string
    return "; ".join({key.strip(): None for key in user_agent.split(";")}.keys())
