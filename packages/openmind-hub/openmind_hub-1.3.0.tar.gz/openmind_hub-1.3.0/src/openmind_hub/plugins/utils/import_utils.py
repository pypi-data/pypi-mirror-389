# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# Copyright 2022 The HuggingFace Inc. team.
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

# This code is borrowed and modified from
# https://github.com/huggingface/transformers/blob/v4.36.0/src/transformers/utils/import_utils.py
import importlib
import importlib.metadata


def _is_package_available(pkg_name: str) -> bool:
    # Check we're not importing a "pkg_name" directory somewhere but the actual library by trying to grab the version
    package_exists = importlib.util.find_spec(pkg_name) is not None
    if package_exists:
        try:
            _ = importlib.metadata.metadata(pkg_name)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False
    return False


def is_openi_available() -> bool:
    return _is_package_available("openi")


def is_hf_available() -> bool:
    return _is_package_available("huggingface_hub")
