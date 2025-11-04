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
from typing import Optional

import requests
from requests import HTTPError, Response

from ..constants import (
    GATE_REPOSITORY,
    ENTRY_NOT_FOUND,
    NOT_ON_WHITE_LIST,
    REF_NOT_EXIST_CODE,
    REVISION_NOT_FOUND,
    REPOSITORY_NOT_FOUND,
    BRANCH_OR_PATH_NOT_FOUND_CODE,
)
from .logging import replace_invalid_characters


def _format_error_message(
    message: str, request_id: Optional[str], server_message: Optional[str], original_message: Optional[str]
) -> str:
    """
    Format the `OmHubHTTPError` error message based on initial message and information
    returned by the server.
    """
    # Add message from response body
    if original_message is not None and original_message.lower() not in message.lower():
        message = f"Original Error: {original_message}\n" + message

    if server_message is not None and len(server_message) > 0 and server_message.lower() not in message.lower():
        if "\n\n" in message:
            message += "\n" + server_message
        else:
            message += "\n\n" + server_message

    # Add Request ID
    if request_id is not None and str(request_id).lower() not in message.lower():
        request_id_message = f" (Request ID: {request_id})"
        if "\n" in message:
            newline_index = message.index("\n")
            message = message[:newline_index] + request_id_message + message[newline_index:]
        else:
            message += request_id_message

    return replace_invalid_characters(message)


class OmHubHTTPError(HTTPError):
    """
    HTTPError to inherit from for any custom HTTP Error raised in Om Hub.

    Any HTTPError is converted at least into a `OmHubHTTPError`. If some information is
    sent back by the server, it will be added to the error message.

    Added details:
    - Request id from "X-Request-Id" header if exists.
    - Server error message from the header "X-Error-Message".
    - Server error message if we can found one in the response body.

    """

    request_id: Optional[str] = None
    server_message: Optional[str] = None

    def __init__(self, message: str, response: Optional[Response] = None):
        # Extract original error message if present
        original_message = str(response.content if response is not None else None)
        # Parse server information if any.
        if response is not None:
            # derived class
            self.request_id = response.headers.get("X-Request-Id")
            try:
                server_data = response.json()
            except ValueError:
                server_data = {}

            # Retrieve server error message from multiple sources
            server_message_from_body = server_data.get("code")

            # Concatenate error messages
            _server_message = ""
            if server_message_from_body:
                if isinstance(server_message_from_body, list):
                    server_message_from_body = "\n".join(server_message_from_body)
                if server_message_from_body not in _server_message:
                    _server_message += server_message_from_body + "\n"
            _server_message = _server_message.strip()

            # Set message to `OmHubHTTPError` (if any)
            if _server_message:
                # derived class
                self.server_message = _server_message
        # base class
        super().__init__(
            _format_error_message(
                message,
                request_id=self.request_id,
                server_message=self.server_message,
                original_message=original_message,
            ),
            response=response,  # type: ignore
            request=response.request if response else None,  # type: ignore
        )


class RepositoryNotFoundError(OmHubHTTPError):
    """
    RepositoryNotFoundError
        >>> from openmind_hub import model_info
        >>> model_info("<non_existent_repository>")

    if repository not exist:
        merlin_hub.utils._errors.RepositoryNotFoundError: 404 Client Error.
        Please make sure you specified the correct `repo_id` and `repo_type`.
    """


class RevisionNotFoundError(OmHubHTTPError):
    """
    RevisionNotFoundError
        >>> from openmind_hub import om_hub_download
        >>> om_hub_download(' Intel/neural-chat-7b-v3-1', 'config.json', revision='<non-existent-revision>')

    if revision not exist:
        RevisionNotFoundError: 404 Client Error.
        Invalid rev id: <non-existent-revision>
    """


class EntryNotFoundError(OmHubHTTPError, FileNotFoundError):
    """
    EntryNotFoundError
        >>> from openmind_hub import om_hub_download
        >>> om_hub_download(' Intel/neural-chat-7b-v3-1', '<non-existent-file>')

    if file do not exist:
        EntryNotFoundError: 404 Client Error.
    """


class GatedRepoError(OmHubHTTPError):
    """GatedRepoError
        >>> from openmind_hub import model_info
        >>> model_info("<gated_repository>")

    if try to access a private repo but do not have the necessary permissions:
        GatedRepoError: 401 Client Error.
    """


class BadRequestError(OmHubHTTPError, ValueError):
    """
    Raised by `om_raise_for_status` when the server returns a HTTP 400 error.
    """


class LocalEntryNotFoundError(EntryNotFoundError, FileNotFoundError, ValueError):
    """
    Raised when trying to access a file that is not on the disk when network is
    disabled or unavailable (connection issue). The entry may exist on the Hub.
    """

    def __init__(self, message: str):
        super().__init__(message, response=None)


class FileMetadataError(OSError):
    """Error triggered when the metadata of a file on the Hub cannot be retrieved (missing ETag or commit_hash).

    Inherits from `OSError` for backward compatibility.
    """


class AccessWhiteListError(OmHubHTTPError):
    """
    Raised when trying to access a file that is not on the disk when network is
    disabled or unavailable (connection issue). The entry may exist on the Hub.
    """

    def __init__(self, message: str):
        super().__init__(message, response=None)


class OMValidationError(ValueError):
    """Generic exception thrown by `openmind` validators.

    Inherits from [`ValueError`]
    """


def om_raise_for_status(response: Response, endpoint_name: Optional[str] = None) -> None:
    if endpoint_name and not isinstance(endpoint_name, str):
        raise TypeError("endpoint_name should be str or None.")
    try:
        response.raise_for_status()
    except HTTPError as e:
        try:
            response_code = response.json().get("code")
        except requests.exceptions.JSONDecodeError:
            response_code = ""
        error_code = response.status_code
        if error_code == REVISION_NOT_FOUND and response_code == REF_NOT_EXIST_CODE:
            message = f"{response.status_code} Client Error." + "\n\n" + f"Revision Not Found for url: {response.url}."
            raise RevisionNotFoundError(message, response) from e

        elif error_code == ENTRY_NOT_FOUND and response_code == BRANCH_OR_PATH_NOT_FOUND_CODE:
            message = f"{response.status_code} Client Error." + "\n\n" + f"Entry Not Found for url: {response.url}."
            raise EntryNotFoundError(message, response) from e

        elif error_code == GATE_REPOSITORY:
            message = (
                f"{response.status_code} Client Error." + "\n\n" + f"Cannot access gated repo for url {response.url}."
            )
            raise GatedRepoError(message, response) from e

        elif error_code == NOT_ON_WHITE_LIST:
            message = f"{response.status_code} Client Error." + "\n\n" + f"Does not on white list {response.url}."
            raise AccessWhiteListError(message) from e

        elif error_code == REPOSITORY_NOT_FOUND:
            message = (
                f"{response.status_code} Client Error."
                + "\n\n"
                + f"Repository Not Found for url: {response.url}. "
                + "\nPlease make sure you specified the correct `repo_id` and"
                " `repo_type`.\nIf you are trying to access a private or gated repo,"
                " make sure you are authenticated."
            )
            raise RepositoryNotFoundError(message, response) from e

        elif response.status_code == 400:
            message = f"\n\nBad request for {endpoint_name} endpoint:" if endpoint_name else "\n\nBad request:"
            raise BadRequestError(message, response=response) from e

        # Convert `HTTPError` into a `OmHubHTTPError` to display request information
        # as well (request id and/or server error message)
        raise OmHubHTTPError(str(e), response=response) from e
