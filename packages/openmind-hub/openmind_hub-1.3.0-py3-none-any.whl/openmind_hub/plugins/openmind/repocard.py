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
import os.path
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from typing import Literal, Optional, Union, Dict, Type

import yaml

from .file_download import om_hub_download
from .om_api import upload_file
from .repocard_data import (
    CardData,
    DatasetCardData,
    model_index_to_eval_results,
    ModelCardData,
)
from .utils import EntryNotFoundError
from .utils.logging import replace_invalid_characters
from .utils._validators import validate_om_hub_args

TEMPLATE_MODELCARD_PATH = Path(__file__).parent / "templates" / "modelcard_template.md"
TEMPLATE_DATASETCARD_PATH = Path(__file__).parent / "templates" / "datasetcard_template.md"
REGEX_YAML_BLOCK = re.compile(r"^(\s*---[\r\n])([\S\s]*?)([\r\n]---(\r\n|\n|$))")


class RepoCard:
    card_data_class = CardData
    default_template_path = TEMPLATE_MODELCARD_PATH
    repo_type = "model"

    def __init__(self, content: str, ignore_metadata_errors: bool = False):
        """Initialize a RepoCard from string content. The content should be a
        Markdown file with a YAML block at the beginning and a Markdown body.

        Args:
            content (`str`): The content of the Markdown file.
        """

        # Set the content of the RepoCard, as well as underlying .data and .text attributes.
        # See the `content` property setter for more details.
        self.ignore_metadata_errors = ignore_metadata_errors
        self.content = content

    def __str__(self):
        return self.content

    @property
    def content(self):
        """The content of the RepoCard, including the YAML block and the Markdown body."""
        line_break = _detect_line_ending(self._content) or "\n"
        return f"---{line_break}{self.data.to_yaml(line_break=line_break)}{line_break}---{line_break}{self.text}"

    @content.setter
    def content(self, content: str):
        """Set the content of the RepoCard."""
        self._content = content

        match = REGEX_YAML_BLOCK.search(content)
        if match:
            # Metadata found in the YAML block
            yaml_block = match.group(2)
            self.text = content[match.end() :]
            data_dict = yaml.safe_load(yaml_block)

            if data_dict is None:
                data_dict = {}

            # The YAML block's data should be a dictionary
            if not isinstance(data_dict, dict):
                raise ValueError("repo card metadata block should be a dict")
        else:
            # Model card without metadata... create empty metadata
            data_dict = {}
            self.text = content

        self.data = self.card_data_class(**data_dict, ignore_metadata_errors=self.ignore_metadata_errors)

    @classmethod
    def load(
        cls,
        repo_id_or_path: Union[str, Path],
        repo_type: Optional[str] = None,
        token: Optional[str] = None,
        ignore_metadata_errors: bool = False,
    ):
        """Initialize a RepoCard from a openMind Hub repo's README.md or a local filepath.

        Args:
            repo_id_or_path (`Union[str, Path]`):
                The repo ID associated with a openMind Hub repo or a local filepath.
            repo_type (`str`, *optional*):
                The type of openMind repo to push to. Defaults to None, which will use "model".
                Other options are "dataset" and "space".
                Not used when loading from a local filepath.
                If this is called from a child class,
                the default value will be the child class's `repo_type`.
            token (`str`, *optional*):
                Authentication token, obtained with `.OmApi.login` method.
                Will default to the stored token.
            ignore_metadata_errors (`str`):
                If True, errors while parsing the metadata section will be ignored. Some
                information might be lost during the process. Use it at your own risk.

        Returns:
            [`.repocard.RepoCard`]:
            The RepoCard (or subclass) initialized from the repo's
                README.md file or filepath.
        """

        if Path(repo_id_or_path).exists():
            card_path = Path(repo_id_or_path)
        elif isinstance(repo_id_or_path, str):
            card_path = Path(
                om_hub_download(
                    repo_id_or_path,
                    "README.md",
                    repo_type=repo_type or cls.repo_type,
                    token=token,
                )
            )
        else:
            raise ValueError(
                replace_invalid_characters(f"Cannot load RepoCard: path not found on disk ({repo_id_or_path}).")
            )

        # Preserve newlines in the existing file.
        with card_path.open(mode="r", newline="", encoding="utf-8") as f:
            return cls(f.read(), ignore_metadata_errors=ignore_metadata_errors)

    @classmethod
    def from_template(
        cls,
        card_data: CardData,
        template_path: Optional[str] = None,
        template_str: Optional[str] = None,
        **template_kwargs,
    ):
        """Initialize a RepoCard from a template. By default, it uses the default template.

        Templates are Jinja2 templates that can be customized by passing keyword arguments.

        Args:
            card_data (`.CardData`):
                A .CardData instance containing the metadata you want to include in the YAML
                header of the repo card on the openMind Hub.
            template_path (`str`, *optional*):
                A path to a markdown file with optional Jinja template variables that can be filled
                in with `template_kwargs`. Defaults to the default template.

        Returns:
            [`.repocard.RepoCard`]: A RepoCard instance with the specified card data and content from the
            template.
        """
        try:
            import jinja2
        except ModuleNotFoundError as execption:
            raise ModuleNotFoundError(
                "Using RepoCard.from_template requires Jinja2 to be installed. Please"
                " install it with `pip install Jinja2`."
            ) from execption

        kwargs = card_data.to_dict().copy()
        kwargs.update(template_kwargs)  # Template_kwargs have priority
        template = jinja2.Template(Path(template_path or cls.default_template_path).read_text())
        content = template.render(card_data=card_data.to_yaml(), **kwargs)
        return cls(content)

    def save(self, filepath: Union[Path, str]):
        r"""Save a RepoCard to a file.

        Args:
            filepath (`Union[Path, str]`): Filepath to the markdown file to save.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        # Preserve newlines as in the existing file.
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            f.write(str(self))

    def push_to_hub(
        self,
        repo_id: str,
        token: Optional[str] = None,
        repo_type: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs,
    ):
        """Push a RepoCard to a openMind Hub repo.

        Args:
            repo_id (`str`):
                The repo ID of the openMind Hub repo to push to.
            token (`str`, *optional*):
                Authentication token, Will default to the stored token.
            repo_type (`str`, *optional*, defaults to "model"):
                The type of openMind repo to push to. Options are "model", "dataset",
                and "space". If this
                function is called by a child class,
                it will default to the child class's `repo_type`.
            commit_message (`str`, *optional*):
                The summary / title / first line of the generated commit.
            commit_description (`str`, *optional*)
                The description of the generated commit.
            revision (`str`, *optional*):
                The git revision to commit from. Defaults to the head of the `"main"` branch.
        """

        # If repo type is provided, otherwise, use the repo type of the card.
        repo_type = repo_type or self.repo_type

        with TemporaryDirectory(dir=os.path.expanduser("~")) as tmpdir:
            tmp_path = Path(tmpdir) / "README.md"
            tmp_path.write_text(str(self))
            upload_file(
                path_or_fileobj=str(tmp_path),
                path_in_repo="README.md",
                repo_id=repo_id,
                token=token,
                repo_type=repo_type,
                commit_message=commit_message,
                commit_description=commit_description,
                revision=revision,
            )


class ModelCard(RepoCard):
    card_data_class = ModelCardData
    default_template_path = TEMPLATE_MODELCARD_PATH
    repo_type = "model"

    @classmethod
    def from_template(  # type: ignore # violates Liskov property but easier to use
        cls,
        card_data: ModelCardData,
        template_path: Optional[str] = None,
        template_str: Optional[str] = None,
        **template_kwargs,
    ):
        """Initialize a ModelCard from a template. By default, it uses the default template.

        Templates are Jinja2 templates that can be customized by passing keyword arguments.

        Args:
            card_data (`.ModelCardData`):
                A .ModelCardData instance containing the metadata you want to include in the YAML
                header of the model card on the openMind
            template_path (`str`, *optional*):
                A path to a markdown file with optional Jinja template variables that can be filled
                in with `template_kwargs`. Defaults to the default template.

        Returns:
            [`.ModelCard`]: A ModelCard instance with the specified card data and content from the
            template.
        """
        return super().from_template(card_data, template_path, template_str, **template_kwargs)


class DatasetCard(RepoCard):
    card_data_class = DatasetCardData
    default_template_path = TEMPLATE_DATASETCARD_PATH
    repo_type = "dataset"

    @classmethod
    def from_template(  # type: ignore # violates Liskov property but easier to use
        cls,
        card_data: DatasetCardData,
        template_path: Optional[str] = None,
        **template_kwargs,
    ):
        """Initialize a DatasetCard from a template. By default, it uses the default template.

        Templates are Jinja2 templates that can be customized by passing keyword arguments.

        Args:
            card_data (`.DatasetCardData`):
                A .DatasetCardData instance containing the metadata you want to include in the YAML
                header of the dataset card on the openMind Hub.
            template_path (`str`, *optional*):
                A path to a markdown file with optional Jinja template variables that can be filled
                in with `template_kwargs`. Defaults to the default template.

        Returns:
            [`.DatasetCard`]: A DatasetCard instance with the specified card data and content from the
            template.
        """
        return super().from_template(card_data, template_path, **template_kwargs)


def _detect_line_ending(content: str) -> Literal["\r", "\n", "\r\n", ""]:
    """Detect the line ending of a string. Used by RepoCard to avoid making diff on newlines.

    Uses same implementation as in Hub server, keep it in sync.

    Returns:
        str: The detected line ending of the string.
    """
    cr = content.count("\r")
    lf = content.count("\n")
    crlf = content.count("\r\n")
    if cr + lf == 0:
        return ""
    if crlf == cr and crlf == lf:
        return "\r\n"
    if cr > lf:
        return "\r"
    else:
        return "\n"


@validate_om_hub_args
def metadata_update(
    repo_id: str,
    metadata: Dict,
    *,
    repo_type: Optional[str] = None,
    overwrite: bool = False,
    token: Optional[str] = None,
    commit_message: Optional[str] = None,
    commit_description: Optional[str] = None,
    revision: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Updates the metadata in the README.md of a repository on the openMind Hub.

    Args:
        repo_id (`str`):
            The name of the repository.
        metadata (`dict`):
            A dictionary containing the metadata to be updated.
        repo_type (`str`, *optional*):
            Set to `"dataset"` or `"space"` if updating to a dataset or space,
            `None` or `"model"` if updating to a model. Default is `None`.
        overwrite (`bool`, *optional*, defaults to `False`):
            If set to `True` an existing field can be overwritten, otherwise
            attempting to overwrite an existing field will cause an error.
        token (`str`, *optional*):
            The openMind authentication token.
        commit_message (`str`, *optional*):
            The summary / title / first line of the generated commit. Defaults to
            `f"Update metadata with openmind"`
        commit_description (`str` *optional*)
            The description of the generated commit
        revision (`str`, *optional*):
            The git revision to commit from. Defaults to the head of the
            `"main"` branch.
    Returns:
        `str`: URL of the commit which updated the card metadata.
    """
    commit_message = commit_message if commit_message is not None else "Update metadata with openmind"

    # Card class given repo_type
    card_class: Type[RepoCard]
    if repo_type is None or repo_type == "model":
        card_class = ModelCard
    elif repo_type == "dataset":
        card_class = DatasetCard
    elif repo_type == "space":
        card_class = RepoCard
    else:
        raise ValueError(replace_invalid_characters(f"Unknown repo_type: {repo_type}"))

    # Either load repo_card from the Hub or create an empty one.
    # NOTE: Will not create the repo if it doesn't exist.
    try:
        card = card_class.load(repo_id, token=token, repo_type=repo_type)
    except EntryNotFoundError as error:
        if repo_type == "space":
            raise ValueError("Cannot update metadata on a Space that doesn't contain a `README.md` file.") from error

        # Initialize a ModelCard or DatasetCard from default template and no data.
        card = card_class.from_template(CardData())

    for key, value in metadata.items():
        if key == "model-index":
            # if the new metadata doesn't include a name, either use existing one or repo name
            if "name" not in value[0]:
                value[0]["name"] = getattr(card, "model_name", repo_id)
            model_name, new_results = model_index_to_eval_results(value)
            if card.data.eval_results is None:
                card.data.eval_results = new_results
                card.data.model_name = model_name
            else:
                existing_results = card.data.eval_results

                # Iterate over new results
                #   Iterate over existing results
                #       If both results describe the same metric but value is different:
                #           If overwrite=True: overwrite the metric value
                #           Else: raise ValueError
                #       Else: append new result to existing ones.
                for new_result in new_results:
                    result_found = False
                    for existing_result in existing_results:
                        if new_result.is_equal_except_value(existing_result):
                            if new_result != existing_result and not overwrite:
                                error_msg = (
                                    "You passed a new value for the existing metric"
                                    f" 'name: {new_result.metric_name}, type: "
                                    f"{new_result.metric_type}'. Set `overwrite=True`"
                                    " to overwrite existing metrics."
                                )
                                raise ValueError(replace_invalid_characters(error_msg))
                            result_found = True
                            existing_result.metric_value = new_result.metric_value
                            if existing_result.verified is True:
                                existing_result.verify_token = new_result.verify_token
                    if not result_found:
                        card.data.eval_results.append(new_result)
        else:
            # Any metadata that is not a result metric
            if card.data.get(key) is not None and not overwrite and card.data.get(key) != value:
                error_msg = (
                    f"You passed a new value for the existing meta data field '{key}'."
                    " Set `overwrite=True` to overwrite existing metadata."
                )
                raise ValueError(replace_invalid_characters(error_msg))
            else:
                card.data[key] = value

    return card.push_to_hub(
        repo_id,
        token=token,
        repo_type=repo_type,
        commit_message=commit_message,
        commit_description=commit_description,
        revision=revision,
    )
