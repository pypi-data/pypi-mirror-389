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
import importlib
import sys
import subprocess
from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Import version.py as a module
version_path = Path(os.path.dirname(os.path.realpath(__file__))) / "src/openmind_hub/version.py"
root_path = str(version_path.parent.resolve())
sys.path.append(root_path)
mod_name = version_path.stem
mod = importlib.import_module(mod_name)
__version__ = mod.__version__


def _get_git_revision_short_hash() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()


def _update_pkg_version(version: str) -> str:
    original_version = version
    try:
        git_sha = _get_git_revision_short_hash()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_sha = ""

    if git_sha and "dev" in original_version:
        new_version = f"{original_version}+{git_sha}"
    else:
        new_version = original_version

    return new_version


with open(root_path + "/git_version_info.py", "w") as fd:
    fd.write(f"__version__='{_update_pkg_version(__version__)}'\n")


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["version"] = _update_pkg_version(__version__)


class CustomBuildHook(BuildHookInterface):
    """A custom build hook for building ."""

    def initialize(self, version, build_data):
        """Initialize the hook."""
        pass
