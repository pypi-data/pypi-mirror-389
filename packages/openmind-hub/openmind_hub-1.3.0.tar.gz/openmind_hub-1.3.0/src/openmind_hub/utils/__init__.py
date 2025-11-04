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

__all__ = [
    "OMValidationError",
    "EntryNotFoundError",
    "RepositoryNotFoundError",
    "RevisionNotFoundError",
    "GatedRepoError",
    "LocalEntryNotFoundError",
    "OmHubHTTPError",
    "om_raise_for_status",
    "build_om_headers",
]


import logging
import os
from typing import Dict, Optional, Union

from openmind_hub.plugins import openmind
from openmind_hub.plugins.utils.import_utils import is_openi_available

logging.warning(
    "`from openmind_hub.utils import` will be discarded in the future. Please use `from openmind_hub import` instead."
)


def get_plugin(platform: str = None):
    platform = platform or os.getenv("platform")
    if platform is None or platform == "openmind":
        module = openmind
    elif platform == "openi":
        if not is_openi_available():
            raise ImportError("openi was not found in your environment. Please install and restart your runtime.")
        from openmind_hub.plugins import openi

        module = openi
    else:
        raise ValueError("unknown platform")
    return module


# 常数和类初始化后不会再变化，函数可以通过设置环境变量或传递`platform`参数决定访问的服务端。
class UtilsApi:
    OMValidationError = get_plugin().OMValidationError
    EntryNotFoundError = get_plugin().EntryNotFoundError
    RepositoryNotFoundError = get_plugin().RepositoryNotFoundError
    RevisionNotFoundError = get_plugin().RevisionNotFoundError
    GatedRepoError = get_plugin().GatedRepoError
    LocalEntryNotFoundError = get_plugin().LocalEntryNotFoundError
    OmHubHTTPError = get_plugin().OmHubHTTPError

    @staticmethod
    def om_raise_for_status(response, endpoint_name: Optional[str] = None, **kwargs):
        module = get_plugin(kwargs.pop("platform", None))
        return module.om_raise_for_status(response=response, endpoint_name=endpoint_name)

    @staticmethod
    def build_om_headers(
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


api = UtilsApi()

om_raise_for_status = api.om_raise_for_status
build_om_headers = api.build_om_headers
OmHubHTTPError = api.OmHubHTTPError
OMValidationError = api.OMValidationError
EntryNotFoundError = api.EntryNotFoundError
RepositoryNotFoundError = api.RepositoryNotFoundError
RevisionNotFoundError = api.RevisionNotFoundError
GatedRepoError = api.GatedRepoError
LocalEntryNotFoundError = api.LocalEntryNotFoundError
