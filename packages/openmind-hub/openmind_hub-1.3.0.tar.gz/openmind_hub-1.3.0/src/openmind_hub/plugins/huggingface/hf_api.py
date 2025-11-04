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
from openmind_hub.interface.base_api import BaseApi
from openmind_hub.plugins.utils.import_utils import is_hf_available

if is_hf_available():
    import huggingface_hub


class HFApi(BaseApi):
    def http_get(self, *args, **kwargs):
        return huggingface_hub.file_download.http_get(*args, **kwargs)

    def om_hub_url(self, *args, **kwargs):
        return huggingface_hub.hf_hub_url(*args, **kwargs)

    def create_repo(self, *args, **kwargs):
        return huggingface_hub.create_repo(*args, **kwargs)

    def create_branch(self, *args, **kwargs):
        return huggingface_hub.create_branch(*args, **kwargs)

    def upload_folder(self, *args, **kwargs):
        return huggingface_hub.upload_folder(*args, **kwargs)

    def upload_file(self, *args, **kwargs):
        return huggingface_hub.upload_file(*args, **kwargs)

    def om_hub_download(self, *args, **kwargs):
        return huggingface_hub.hf_hub_download(*args, **kwargs)

    def snapshot_download(self, *args, **kwargs):
        return huggingface_hub.snapshot_download(*args, **kwargs)

    def build_om_headers(self, *args, **kwargs):
        return huggingface_hub.utils.build_hf_headers(*args, **kwargs)

    def om_raise_for_status(self, *args, **kwargs):
        return huggingface_hub.utils.hf_raise_for_status(*args, **kwargs)

    def try_to_load_from_cache(self, *args, **kwargs):
        return huggingface_hub.try_to_load_from_cache(*args, **kwargs)


hf_api = HFApi()

OM_HOME = hf_api.OM_HOME
OM_HUB_CACHE = hf_api.OM_HUB_CACHE
REGEX_COMMIT_HASH = hf_api.REGEX_COMMIT_HASH
default_cache_path = hf_api.default_cache_path
_CACHED_NO_EXIST = hf_api._CACHED_NO_EXIST
ENDPOINT = hf_api.ENDPOINT
upload_file = hf_api.upload_file
upload_folder = hf_api.upload_folder
create_commit = hf_api.create_commit
om_hub_download = hf_api.om_hub_download
snapshot_download = hf_api.snapshot_download
get_om_file_metadata = hf_api.get_om_file_metadata
om_hub_url = hf_api.om_hub_url
http_get = hf_api.http_get
try_to_load_from_cache = hf_api.try_to_load_from_cache
create_repo = hf_api.create_repo
delete_repo = hf_api.delete_repo
repo_info = hf_api.repo_info
model_info = hf_api.model_info
list_models = hf_api.list_models
dataset_info = hf_api.dataset_info
list_datasets = hf_api.list_datasets
list_metrics = hf_api.list_metrics
space_info = hf_api.space_info
list_spaces = hf_api.list_spaces
restart_space = hf_api.restart_space
list_repo_tree = hf_api.list_repo_tree
whoami = hf_api.whoami
create_branch = hf_api.create_branch
delete_branch = hf_api.delete_branch
get_full_repo_name = hf_api.get_full_repo_name
OmApi = hf_api.OmApi
RepoUrl = hf_api.RepoUrl
RepoFile = hf_api.RepoFile
RepoFolder = hf_api.RepoFolder
ModelInfo = hf_api.ModelInfo
ModelFilter = hf_api.ModelFilter
DatasetInfo = hf_api.DatasetInfo
CommitOperationAdd = hf_api.CommitOperationAdd
CommitOperationDelete = hf_api.CommitOperationDelete
Repository = hf_api.Repository
DatasetCard = hf_api.DatasetCard
DatasetCardData = hf_api.DatasetCardData
metadata_update = hf_api.metadata_update
OmFileSystem = hf_api.OmFileSystem
OmHubHTTPError = hf_api.OmHubHTTPError
GatedRepoError = hf_api.GatedRepoError
OMValidationError = hf_api.OMValidationError
EntryNotFoundError = hf_api.EntryNotFoundError
AccessWhiteListError = hf_api.AccessWhiteListError
RevisionNotFoundError = hf_api.RevisionNotFoundError
RepositoryNotFoundError = hf_api.RepositoryNotFoundError
LocalEntryNotFoundError = hf_api.LocalEntryNotFoundError
om_raise_for_status = hf_api.om_raise_for_status
build_om_headers = hf_api.build_om_headers
