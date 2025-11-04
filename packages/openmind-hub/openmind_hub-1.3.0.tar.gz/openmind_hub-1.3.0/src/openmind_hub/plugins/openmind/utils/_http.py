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
from functools import lru_cache
from http import HTTPStatus
import os
import ssl
import threading
import time
from typing import Callable, Tuple, Type, Union

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from ..constants import CUSTOM_CIPHERS, DEFAULT_REQUEST_TIMEOUT, MAX_RESPONSE_SIZE, HttpMethodList
from .logging import get_logger


logger = get_logger(__name__)


class CustomCipherAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLS_CLIENT, ciphers=":".join(CUSTOM_CIPHERS))
        context.mininum_version = ssl.TLSVersion.TLSv1_2
        kwargs["ssl_context"] = context
        return super(CustomCipherAdapter, self).init_poolmanager(*args, **kwargs)


def reset_sessions() -> None:
    """Reset the cache of sessions.

    Mostly used internally when sessions are reconfigured or an SSLError is raised.
    """
    _get_session_from_cache.cache_clear()


def http_backoff(
    method: HttpMethodList,
    url: str,
    *,
    max_retries: int = 10,
    base_wait_time: float = 1,
    max_wait_time: float = 8,
    retry_on_exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (
        requests.Timeout,
        requests.ConnectionError,
    ),
    timeout: Union[int, float] = DEFAULT_REQUEST_TIMEOUT,
    retry_on_status_codes: Union[int, Tuple[int, ...]] = HTTPStatus.SERVICE_UNAVAILABLE,
    **kwargs,
) -> Response:
    if isinstance(retry_on_exceptions, type):  # Tuple from single exception type
        retry_on_exceptions = (retry_on_exceptions,)

    if isinstance(retry_on_status_codes, int):  # Tuple from single status code
        retry_on_status_codes = (retry_on_status_codes,)

    nb_tries = 0
    sleep_time = base_wait_time

    # If `data` is used and is a file object (or any IO), it will be consumed on the
    # first HTTP request. We need to save the initial position so that the full content
    # of the file is re-sent on http backoff. See warning tip in docstring.
    io_obj_initial_pos = None
    data = kwargs.get("data")
    if data:
        io_obj_initial_pos = data.tell()

    session = get_session()
    while True:
        nb_tries += 1
        try:
            if io_obj_initial_pos is not None:
                data.seek(io_obj_initial_pos)

            logger.debug("_upload_parts_iteratively send HTTPS request")
            response = session.request(method=method, url=url, timeout=DEFAULT_REQUEST_TIMEOUT, **kwargs)

            if response.status_code not in retry_on_status_codes:
                return response

            if nb_tries > max_retries:
                response.raise_for_status()
                return response

        except retry_on_exceptions as err:
            if isinstance(err, requests.ConnectionError):
                logger.warning("ConnectionError occurred during request. Retrying...")
                reset_sessions()

            if isinstance(err, requests.Timeout):
                logger.warning("Timeout occurred during request. Retrying...")

            if nb_tries > max_retries:
                logger.error("Max retries exceeded. Unable to recover from error.")
                raise err

        # Sleep for X seconds
        time.sleep(sleep_time)

        # Update sleep time for next retry
        sleep_time = min(max_wait_time, sleep_time * 2)  # Exponential backoff


def _default_backend_factory() -> requests.Session:
    session = requests.Session()
    session.mount("https://", CustomCipherAdapter())
    session.hooks["response"] = [limit_response_size]
    return session


BackFactoryList = Callable[[], requests.Session]
_GLOBAL_BACKEND_FACTORY: BackFactoryList = _default_backend_factory


@lru_cache
def _get_session_from_cache(process_id: int, thread_id: int) -> requests.Session:
    """
    Create a new session per thread using global factory.
    Using LRU cache (maxsize 128) to avoid memory leaks when
    using thousands of threads.
    """
    return _GLOBAL_BACKEND_FACTORY()


def get_session() -> requests.Session:
    """
    Get a `requests.Session` object, using the session factory from the user.

    Use [`get_session`] to get a configured Session. Since `requests.Session` is not guaranteed to be thread-safe,
    create 1 Session instance per thread.
    """
    return _get_session_from_cache(process_id=os.getpid(), thread_id=threading.get_ident())


def limit_response_size(response: Response, *args, **kwargs):
    bytes_read = 0
    content = b""
    for chunk in response.iter_content(chunk_size=1024):
        bytes_read += len(chunk)
        content += chunk
        if bytes_read > MAX_RESPONSE_SIZE:
            raise ValueError(f"Response size error, more than {MAX_RESPONSE_SIZE}")
    response._content_consumed = False
    response._content = content
