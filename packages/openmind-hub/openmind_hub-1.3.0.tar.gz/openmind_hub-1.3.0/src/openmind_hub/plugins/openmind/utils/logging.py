# Copyright 2020 Optuna, Hugging Face
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
# Note: This file is mainly copied from transformers.logger

import copy
import logging
import threading

from tqdm import auto as tqdm_lib


_lock = threading.Lock()
GLOBAL_HANDLER = None
TQDM_ACTIVE = True

log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
LOG_CONTENT_BLACK_LIST = [
    "\r",
    "\n",
    "\t",
    "\f",
    "\v",
    "\b",
    "\u000a",
    "\u000d",
    "\u000c",
    "\u000b",
    "\u0008",
    "\u007f",
    "\u0009",
]
BLANKS = "    "

DEFAULT_LOG_LEVEL = logging.WARNING


def replace_invalid_characters(content: str, allow_line_separator=False) -> str:
    """Find and replace invalid characters in input content"""
    if not isinstance(content, str):
        raise TypeError("Input content for replacing invalid characters should be string format.")

    black_list_bak = copy.deepcopy(LOG_CONTENT_BLACK_LIST)

    if allow_line_separator:
        black_list_bak.remove("\n")

    for forbidden_str in black_list_bak:
        if forbidden_str in content:
            content = content.replace(forbidden_str, "")

    while BLANKS in content:
        content = content.replace(BLANKS, " ")

    return content


def set_verbosity(verbosity: int) -> None:
    """Set the verbosity level for root logger"""

    _configure_library_root_logger()
    get_logger().setLevel(verbosity)


def set_verbosity_info():
    """Set the verbosity to the `INFO` level."""
    info = log_levels.get("info", None)
    if not info:
        raise ValueError("can't get info from log_levels dict")
    return set_verbosity(info)


def set_verbosity_warning():
    """Set the verbosity to the `WARNING` level."""
    warning = log_levels.get("warning", None)
    if not warning:
        raise ValueError("can't get warning from log_levels dict")
    return set_verbosity(warning)


def set_verbosity_debug():
    """Set the verbosity to the `DEBUG` level."""
    debug = log_levels.get("debug", None)
    if not debug:
        raise ValueError("can't get debug from log_levels dict")
    return set_verbosity(debug)


def set_verbosity_error():
    """Set the verbosity to the `ERROR` level."""
    error = log_levels.get("error", None)
    if not error:
        raise ValueError("can't get error from log_levels dict")
    return set_verbosity(error)


def set_verbosity_critical():
    """Set the verbosity to the `CRITICAL` level."""
    critical = log_levels.get("critical", None)
    if not critical:
        raise ValueError("can't get critical from log_levels dict")
    return set_verbosity(critical)


def _get_library_name() -> str:
    return __name__.split(".")[0]


class EmptyTqdm:
    """Dummy tqdm which doesn't do anything."""

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self._iterator = args[0] if args else None

    def __iter__(self):
        return iter(self._iterator)

    @staticmethod
    def __getattr__(_):
        """Return empty function."""

        def empty_fn(*args, **kwargs):  # pylint: disable=unused-argument
            return

        return empty_fn

    def __enter__(self):
        return self

    @staticmethod
    def __exit__(type_, value, traceback):
        return


class TqdmCls:
    def __init__(self):
        self._lock = None

    @staticmethod
    def __call__(*args, **kwargs):
        if TQDM_ACTIVE:
            return tqdm_lib.tqdm(*args, **kwargs)
        else:
            return EmptyTqdm(*args, **kwargs)

    @staticmethod
    def get_lock():
        if TQDM_ACTIVE:
            return tqdm_lib.tqdm.get_lock()
        return None

    def set_lock(self, *args, **kwargs):
        """set lock"""
        self._lock = None
        if TQDM_ACTIVE:
            return tqdm_lib.tqdm.set_lock(*args, **kwargs)
        return None


tqdm = TqdmCls()


def _configure_library_root_logger():
    global GLOBAL_HANDLER
    with _lock:
        if GLOBAL_HANDLER:
            return
        GLOBAL_HANDLER = logging.StreamHandler()
        GLOBAL_HANDLER.setFormatter(logging.Formatter("[%(levelname)s][%(asctime)s]: %(message)s"))
        # Apply our default configuration to the library root logger.
        library_root_logger = logging.getLogger(_get_library_name())
        library_root_logger.addHandler(GLOBAL_HANDLER)
        library_root_logger.setLevel(DEFAULT_LOG_LEVEL)
        library_root_logger.propagate = False


class StringFilter(logging.Filter):
    """
    replace some keywords for logger
    """

    def __init__(self, allow_line_separator=False):
        super().__init__()
        self.allow_line_separator = allow_line_separator

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = replace_invalid_characters(record.msg, allow_line_separator=self.allow_line_separator)
        return True


def get_logger(name=None, allow_line_separator=False) -> logging.Logger:
    """
    Return a logger with the specified name. If name is not specified, return the root
    logger
    """
    if not name:
        name = _get_library_name()

    _configure_library_root_logger()
    logger = logging.getLogger(name)
    logger.addFilter(StringFilter(allow_line_separator=allow_line_separator))
    return logger
