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
from openmind_hub.plugins.utils.import_utils import is_openi_available

if is_openi_available():
    from openi.adaptor import om_hub


class OpeniApi(BaseApi):
    CommitOperationAdd = om_hub.CommitOperationAdd

    def http_get(self, *args, **kwargs):
        return om_hub.http_get(*args, **kwargs)

    def om_hub_url(self, *args, **kwargs):
        return om_hub.om_hub_url(*args, **kwargs)

    def create_repo(self, *args, **kwargs):
        return om_hub.create_repo(*args, **kwargs)

    def create_commit(self, *args, **kwargs):
        return om_hub.create_commit(*args, **kwargs)

    def create_branch(self, *args, **kwargs):
        return om_hub.create_branch(*args, **kwargs)

    def upload_folder(self, *args, **kwargs):
        return om_hub.upload_folder(*args, **kwargs)

    def om_hub_download(self, *args, **kwargs):
        return om_hub.om_hub_download(*args, **kwargs)

    def snapshot_download(self, *args, **kwargs):
        return om_hub.snapshot_download(*args, **kwargs)

    def build_om_headers(self, *args, **kwargs):
        return om_hub.build_om_headers(*args, **kwargs)

    def om_raise_for_status(self, *args, **kwargs):
        return om_hub.om_raise_for_status(*args, **kwargs)

    def try_to_load_from_cache(self, *args, **kwargs):
        return om_hub.try_to_load_from_cache(*args, **kwargs)


openi_api = OpeniApi()

OM_HOME = openi_api.OM_HOME
OM_HUB_CACHE = openi_api.OM_HUB_CACHE
REGEX_COMMIT_HASH = openi_api.REGEX_COMMIT_HASH
default_cache_path = openi_api.default_cache_path
_CACHED_NO_EXIST = openi_api._CACHED_NO_EXIST
ENDPOINT = openi_api.ENDPOINT
upload_file = openi_api.upload_file
upload_folder = openi_api.upload_folder
create_commit = openi_api.create_commit
om_hub_download = openi_api.om_hub_download
snapshot_download = openi_api.snapshot_download
get_om_file_metadata = openi_api.get_om_file_metadata
om_hub_url = openi_api.om_hub_url
http_get = openi_api.http_get
try_to_load_from_cache = openi_api.try_to_load_from_cache
create_repo = openi_api.create_repo
delete_repo = openi_api.delete_repo
repo_info = openi_api.repo_info
model_info = openi_api.model_info
list_models = openi_api.list_models
dataset_info = openi_api.dataset_info
list_datasets = openi_api.list_datasets
list_metrics = openi_api.list_metrics
space_info = openi_api.space_info
list_spaces = openi_api.list_spaces
restart_space = openi_api.restart_space
list_repo_tree = openi_api.list_repo_tree
whoami = openi_api.whoami
create_branch = openi_api.create_branch
delete_branch = openi_api.delete_branch
get_full_repo_name = openi_api.get_full_repo_name
OmApi = openi_api.OmApi
RepoUrl = openi_api.RepoUrl
RepoFile = openi_api.RepoFile
RepoFolder = openi_api.RepoFolder
ModelInfo = openi_api.ModelInfo
ModelFilter = openi_api.ModelFilter
DatasetInfo = openi_api.DatasetInfo
CommitOperationAdd = openi_api.CommitOperationAdd
CommitOperationDelete = openi_api.CommitOperationDelete
Repository = openi_api.Repository
DatasetCard = openi_api.DatasetCard
DatasetCardData = openi_api.DatasetCardData
metadata_update = openi_api.metadata_update
OmFileSystem = openi_api.OmFileSystem
OmHubHTTPError = openi_api.OmHubHTTPError
GatedRepoError = openi_api.GatedRepoError
OMValidationError = openi_api.OMValidationError
EntryNotFoundError = openi_api.EntryNotFoundError
AccessWhiteListError = openi_api.AccessWhiteListError
RevisionNotFoundError = openi_api.RevisionNotFoundError
RepositoryNotFoundError = openi_api.RepositoryNotFoundError
LocalEntryNotFoundError = openi_api.LocalEntryNotFoundError
om_raise_for_status = openi_api.om_raise_for_status
build_om_headers = openi_api.build_om_headers
