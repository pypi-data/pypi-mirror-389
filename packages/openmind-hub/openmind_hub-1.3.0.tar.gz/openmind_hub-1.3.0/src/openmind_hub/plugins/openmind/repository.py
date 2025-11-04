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
import atexit
from contextlib import contextmanager
import gc
from logging import ERROR
import os
from pathlib import Path
import re
import subprocess
from subprocess import Popen
import threading
import time
from typing import Callable, Dict, Iterator, List, Optional, Tuple, TypedDict, Union
from urllib.parse import urlparse

from .constants import HUB_GIT_PUSH_TIMEOUT, ONE_MEGABYTE, ENDPOINT
from .om_api import repo_type_and_id_from_om_id
from .file_download import soft_temporary_directory
from .utils._subprocess import run_subprocess
from .utils.logging import get_logger, replace_invalid_characters
from .utils.tqdm_hub import Tqdm
from .utils._validators import validate_om_hub_args, is_sensitive_path, validate_url, validate_repo_id

logger = get_logger(__name__)


class CommandInProgress:
    """
    Utility to follow commands launched asynchronously.
    """

    def __init__(
        self,
        title: str,
        is_done_method: Callable,
        status_method: Callable,
        process: subprocess.Popen,
        post_method: Optional[Callable] = None,
    ):
        self.title = title
        self._is_done = is_done_method
        self._status = status_method
        self._process = process
        self._stderr = ""
        self._stdout = ""
        self._post_method = post_method

    def __repr__(self):
        status = self.status

        if status == -1:
            status = "running"

        return (
            f"[{self.title} command, status code: {status},"
            f" {'in progress.' if not self.is_done else 'finished.'} PID:"
            f" {self._process.pid}]"
        )

    @property
    def is_done(self) -> bool:
        """
        Whether the process is done.
        """
        result = self._is_done()

        if result and self._post_method:
            self._post_method()
            self._post_method = None

        return result

    @property
    def status(self) -> int:
        """
        The exit code/status of the current action. Will return `0` if the
        command has completed successfully, and a number between 1 and 255 if
        the process errored-out.

        Will return -1 if the command is still ongoing.
        """
        return self._status()

    @property
    def failed(self) -> bool:
        """
        Whether the process errored-out.
        """
        return self.status > 0

    @property
    def stderr(self) -> str:
        """
        The current output message on the standard error.
        """
        if self._process.stderr:
            self._stderr += self._process.stderr.read()
        return self._stderr

    @property
    def stdout(self) -> str:
        """
        The current output message on the standard output.
        """
        if self._process.stdout:
            self._stdout += self._process.stdout.read()
        return self._stdout

    def get_process(self):
        """get _process"""
        return self._process


def is_git_repo(folder: Union[str, Path]) -> bool:
    """
    Check if the folder is the root or part of a git repository

    Args:
        folder (`str`):
            The folder in which to run the command.

    Returns:
        `bool`: `True` if the repository is part of a repository, `False`
        otherwise.
    """
    folder_exists = os.path.exists(os.path.join(folder, ".git"))
    git_branch = subprocess.run(
        "git branch".split(), cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False
    )
    return folder_exists and git_branch.returncode == 0


def is_local_clone(folder: Union[str, Path], remote_url: str) -> bool:
    """
    Check if the folder is a local clone of the remote_url

    Args:
        folder (`str` or `Path`):
            The folder in which to run the command.
        remote_url (`str`):
            The url of a git repository.

    Returns:
        `bool`: `True` if the repository is a local clone of the remote
        repository specified, `False` otherwise.
    """
    if not is_git_repo(folder):
        return False

    remotes = run_subprocess("git remote -v", folder).stdout

    # Remove token for the test with remotes.
    remote_url = re.sub(r"https://.*@", "https://", remote_url).rstrip(".git")
    remotes = [re.sub(r"https://.*@", "https://", remote).rstrip(".git") for remote in remotes.split()]
    return remote_url in remotes


def is_tracked_with_lfs(filename: Union[str, Path]) -> bool:
    """
    Check if the file passed is tracked with git-lfs.

    Args:
        filename (`str` or `Path`):
            The filename to check.

    Returns:
        `bool`: `True` if the file passed is tracked with git-lfs, `False`
        otherwise.
    """
    folder = Path(filename).parent
    filename = Path(filename).name

    try:
        p = run_subprocess("git check-attr -a".split() + [filename], folder)
        attributes = p.stdout.strip()
    except subprocess.CalledProcessError as exc:
        if not is_git_repo(folder):
            return False
        else:
            raise OSError(replace_invalid_characters(exc.stderr)) from exc

    if not attributes:
        return False

    found_lfs_tag = {"diff": False, "merge": False, "filter": False}

    for attribute in attributes.split("\n"):
        for tag in found_lfs_tag.keys():
            if tag in attribute and "lfs" in attribute:
                found_lfs_tag[tag] = True

    return all(found_lfs_tag.values())


def is_git_ignored(filename: Union[str, Path]) -> bool:
    """
    Check if file is git-ignored. Supports nested .gitignore files.

    Args:
        filename (`str` or `Path`):
            The filename to check.

    Returns:
        `bool`: `True` if the file passed is ignored by `git`, `False`
        otherwise.
    """
    folder = Path(filename).parent
    filename = Path(filename).name

    try:
        p = run_subprocess("git check-ignore".split() + [filename], folder, check=False)
        # Will return exit code 1 if not gitignored
        is_ignored = not bool(p.returncode)
    except subprocess.CalledProcessError as exc:
        raise OSError(replace_invalid_characters(exc.stderr)) from exc

    return is_ignored


def is_binary_file(filename: Union[str, Path]) -> bool:
    """
    Check if file is a binary file.

    Args:
        filename (`str` or `Path`):
            The filename to check.

    Returns:
        `bool`: `True` if the file passed is a binary file, `False` otherwise.
    """
    try:
        with open(filename, "rb") as f:
            content = f.read(10 * ONE_MEGABYTE)  # Read a maximum of 10MB

        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})
        return bool(content.translate(None, text_chars))
    except UnicodeDecodeError:
        return True


def files_to_be_staged(pattern: str = ".", folder: Union[str, Path, None] = None) -> List[str]:
    """
    Returns a list of filenames that are to be staged.

    Args:
        pattern (`str` or `Path`):
            The pattern of filenames to check. Put `.` to get all files.
        folder (`str` or `Path`):
            The folder in which to run the command.

    Returns:
        `List[str]`: List of files that are to be staged.
    """
    try:
        p = run_subprocess("git ls-files --exclude-standard -mo".split() + [pattern], folder)
        if len(p.stdout.strip()):
            files = p.stdout.strip().split("\n")
        else:
            files = []
    except subprocess.CalledProcessError as exc:
        raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    return files


class PbarT(TypedDict):
    # Used to store an opened progress bar in `_lfs_log_progress`
    bar: Tqdm
    past_bytes: int


@contextmanager
def _lfs_log_progress():
    """
    This is a context manager that will log the Git LFS progress of cleaning,
    smudging, pulling and pushing.
    """

    if logger.getEffectiveLevel() >= ERROR:
        yield
        return

    def output_progress(stopping_event: threading.Event):
        """
        To be launched as a separate thread with an event meaning it should stop
        the tail.
        """
        # Key is tuple(state, filename), value is a dict(tqdm bar and a previous value)
        pbars: Dict[Tuple[str, str], PbarT] = {}

        def close_pbars():
            for pbar in pbars.values():
                bar = pbar.get("bar", None)
                if not bar:
                    raise KeyError("bar is None")
                past_bytes = pbar.get("past_bytes", None)
                if not past_bytes:
                    raise KeyError("past_bytes is None")
                bar.update(bar.total - past_bytes)
                bar.refresh()
                bar.close()

        def tail_file(filename) -> Iterator[str]:
            """
            Creates a generator to be iterated through, which will return each
            line one by one. Will stop tailing the file if the stopping_event is
            set.
            """
            with open(filename, "r") as file:
                current_line = ""
                while True:
                    if stopping_event.is_set():
                        close_pbars()
                        break

                    line_bit = file.readline()
                    if line_bit and line_bit.strip():
                        current_line += line_bit
                        if current_line.endswith("\n"):
                            yield current_line
                            current_line = ""
                    else:
                        time.sleep(1)

        # If the file isn't created yet, wait for a few seconds before trying again.
        # Can be interrupted with the stopping_event.
        git_lfs_progress = os.environ.get("GIT_LFS_PROGRESS")
        while not os.path.exists(git_lfs_progress):
            if stopping_event.is_set():
                close_pbars()
                return

            time.sleep(2)

        for line in tail_file(git_lfs_progress):
            try:
                state, _, byte_progress, filename = line.split()
            except ValueError as error:
                raise ValueError(f"Cannot unpack LFS progress line:\n{line}") from error
            description = replace_invalid_characters(f"{state.capitalize()} file {filename}")

            current_bytes, total_bytes = byte_progress.split("/")
            current_bytes_int = int(current_bytes)
            total_bytes_int = int(total_bytes)

            pbar = pbars.get((state, filename))
            if not pbar:
                # Initialize progress bar
                pbars[(state, filename)] = {
                    "bar": Tqdm(
                        desc=description,
                        initial=current_bytes_int,
                        total=total_bytes_int,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                    ),
                    "past_bytes": int(current_bytes),
                }
            else:
                # Update progress bar
                pbar["bar"].update(current_bytes_int - pbar["past_bytes"])
                pbar["past_bytes"] = current_bytes_int

    current_lfs_progress_value = os.environ.get("GIT_LFS_PROGRESS", "")

    with soft_temporary_directory() as tmp_dir:
        os.environ["GIT_LFS_PROGRESS"] = os.path.join(tmp_dir, "lfs_progress")
        logger.debug(f"Following progress in {os.environ['GIT_LFS_PROGRESS']}")

        exit_event = threading.Event()
        x = threading.Thread(target=output_progress, args=(exit_event,), daemon=True)
        x.start()

        try:
            yield
        finally:
            exit_event.set()
            x.join()

            os.environ["GIT_LFS_PROGRESS"] = current_lfs_progress_value


class Repository:
    command_queue: List[CommandInProgress]

    @validate_om_hub_args
    def __init__(
        self,
        local_dir: Union[str, Path],
        clone_from: Optional[str] = None,
        git_user: Optional[str] = None,
        git_email: Optional[str] = None,
        revision: Optional[str] = None,
        skip_lfs_files: bool = False,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """
        Instantiate a local clone of a git repo.

        If `clone_from` is set, the repo will be cloned from an existing remote repository.
        If the remote repo does not exist, a `EnvironmentError` exception will be thrown.
        Please create the remote repo first using [`create_repo`].

        `Repository` uses the local git credentials by default. If explicitly set, the
        `git_user`/`git_email` pair will be used instead.

        Args:
            local_dir (`str` or `Path`):
                path (e.g. `'my_trained_model/'`) to the local directory, where
                the `Repository` will be initialized.
            clone_from (`str`, *optional*):
                Either a repository url or `repo_id`.
            git_user (`str`, *optional*):
                will override the `git config user.name` for committing and
                pushing files to the hub.
            git_email (`str`, *optional*):
                will override the `git config user.email` for committing and
                pushing files to the hub.
            revision (`str`, *optional*):
                Revision to check out after initializing the repository. If the
                revision doesn't exist, a branch will be created with that
                revision name from the default branch's current HEAD.
            skip_lfs_files (`bool`, *optional*, defaults to `False`):
                whether to skip git-LFS files or not.

        Raises:
            - [`EnvironmentError`](https://docs.python.org/3/library/exceptions.html#EnvironmentError)
              if the remote repository set in `clone_from` does not exist.
        """
        if isinstance(local_dir, Path):
            local_dir = str(local_dir)
        is_sensitive_path(local_dir)
        logger.info(f"making dir: {local_dir}")
        os.makedirs(local_dir, exist_ok=True)
        self.local_dir = os.path.join(os.getcwd(), local_dir)
        self.command_queue = []
        self.skip_lfs_files = skip_lfs_files
        self.check_git_versions()
        self.endpoint = endpoint or ENDPOINT

        if clone_from:
            self.clone_from(repo_url=clone_from)
        else:
            if is_git_repo(self.local_dir):
                logger.debug("[Repository] is a valid git repo")
            else:
                raise ValueError("If not specifying `clone_from`, you need to pass Repository a valid git clone.")

        if not self.check_git_config():
            if git_user and git_email:
                self.git_config_username_and_email(git_user, git_email)
            else:
                logger.warning("Git config is not set, please add git_user and git_email or set git config manually.")

        if revision:
            self.git_checkout(revision, create_branch_ok=True)

        # This ensures that all commands exit before exiting the Python runtime.
        # This will ensure all pushes register on the hub, even if other errors happen in subsequent operations.
        atexit.register(self.wait_for_commands)

    @property
    def current_branch(self) -> str:
        """
        Returns the current checked out branch.

        Returns:
            `str`: Current checked out branch.
        """
        try:
            result = run_subprocess("git rev-parse --abbrev-ref HEAD", self.local_dir).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

        return result

    @property
    def commands_failed(self):
        """
        Returns the asynchronous commands that failed.
        """
        return [c for c in self.command_queue if c.status > 0]

    @property
    def commands_in_progress(self):
        """
        Returns the asynchronous commands that are currently in progress.
        """
        return [c for c in self.command_queue if not c.is_done]

    def check_git_versions(self):
        """
        Checks that `git` and `git-lfs` can be run.

        Raises:
            - [`EnvironmentError`](https://docs.python.org/3/library/exceptions.html#EnvironmentError)
              if `git` or `git-lfs` are not installed.
        """
        try:
            git_version = run_subprocess("git --version", self.local_dir).stdout.strip()
        except FileNotFoundError as exc:
            raise EnvironmentError("Looks like you do not have git installed, please install.") from exc

        logger.info(git_version)

    def clone_from(self, repo_url: str):
        """
        Clone from a remote. If the folder already exists, will try to clone the
        repository within it.

        If this folder is a git repository with linked history, will try to
        update the repository.

        Args:
            repo_url (`str`):
                The URL from which to clone the repository

        <Tip>

        Raises the following error:
            - [`EnvironmentError`](https://docs.python.org/3/library/exceptions.html#EnvironmentError)
              if you are trying to clone the repository in a non-empty folder, or if the
              `git` operations raise errors.

        </Tip>
        """
        if urlparse(repo_url).scheme:
            validate_url(repo_url)
        else:
            validate_repo_id(repo_url)
        hub_url = self.endpoint
        if hub_url in repo_url or ("https" not in repo_url and len(repo_url.split("/")) <= 2):
            repo_type, namespace, repo_name = repo_type_and_id_from_om_id(repo_url, hub_url=hub_url)
            repo_id = f"{namespace}/{repo_name}" if namespace else repo_name
            repo_url = hub_url + "/" + repo_id

        clean_repo_url = re.sub(r"(https?)://.*@", r"\1://", repo_url)
        try:
            run_subprocess("git lfs install", self.local_dir)

            # checks if repository is initialized in an empty repository or in one with files
            if not os.listdir(self.local_dir):
                logger.warning(f"Cloning {clean_repo_url} into local empty directory.")

                with _lfs_log_progress():
                    env = os.environ.copy()
                    env.update({"GIT_ASKPASS": "true"})

                    if self.skip_lfs_files:
                        env.update({"GIT_LFS_SKIP_SMUDGE": "1"})

                    run_subprocess(
                        # 'git lfs clone' is deprecated (will display a warning in the terminal)
                        # but we still use it as it provides a nicer UX when downloading large
                        # files (shows progress).
                        "git clone -c credential.helper=store -c core.askPass=true".split() + [repo_url] + ["."],
                        self.local_dir,
                        env=env,
                    )
            else:
                # Check if the folder is the root of a git repository
                if not is_git_repo(self.local_dir):
                    error_msg = (
                        "Tried to clone a repository in a non-empty folder that isn't"
                        f" a git repository ('{self.local_dir}'). If you really want to"
                        f" do this, do it manually:\n cd {self.local_dir} && git init"
                        " && git remote add origin && git pull origin main\n or clone"
                        " repo to a new folder and move your existing files there"
                        " afterwards."
                    )
                    raise EnvironmentError(replace_invalid_characters(error_msg))

                if is_local_clone(self.local_dir, repo_url):
                    logger.warning(
                        f"{self.local_dir} is already a clone of {clean_repo_url}."
                        " Make sure you pull the latest changes with"
                        " `repo.git_pull()`."
                    )
                else:
                    output = run_subprocess("git remote get-url origin", self.local_dir, check=False)

                    error_msg = (
                        f"Tried to clone {clean_repo_url} in an unrelated git"
                        " repository.\nIf you believe this is an error, please add"
                        f" a remote with the following URL: {clean_repo_url}. "
                    )
                    if output.returncode == 0:
                        clean_local_remote_url = re.sub(r"https://.*@", "https://", output.stdout)
                        error_msg += f"\nLocal path has its origin defined as: {clean_local_remote_url}"
                    raise EnvironmentError(replace_invalid_characters(error_msg))

        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(
                replace_invalid_characters(str(exc.stderr).replace(repo_url, clean_repo_url)),
                "Authentication failed indicates that token is reuqired. One way is setting git"
                " credential.helper to automatically use token."
                " See docs/zh/developer_tutorial/trouble_shooting.md.",
            ) from None

        del repo_url
        gc.collect()

    def check_git_config(self):
        try:
            output1 = run_subprocess("git config user.name", self.local_dir)
            output2 = run_subprocess("git config user.email", self.local_dir)
            if output1.stdout and output2.stdout:
                return True
            return False
        except subprocess.CalledProcessError:
            return False

    def git_config_username_and_email(self, git_user: Optional[str] = None, git_email: Optional[str] = None):
        """
        Sets git username and email (only in the current repo).

        Args:
            git_user (`str`, *optional*):
                The username to register through `git`.
            git_email (`str`, *optional*):
                The email to register through `git`.
        """
        try:
            if git_user and isinstance(git_user, str):
                run_subprocess("git config user.name".split() + [git_user], self.local_dir)

            if git_email and isinstance(git_email, str):
                run_subprocess("git config user.email".split() + [git_email], self.local_dir)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def git_checkout(self, revision: str, create_branch_ok: bool = False):
        """
        git checkout a given revision

        Specifying `create_branch_ok` to `True` will create the branch to the
        given revision if that revision doesn't exist.

        Args:
            revision (`str`):
                The revision to check out.
            create_branch_ok (`str`, *optional*, defaults to `False`):
                Whether creating a branch named with the `revision` passed at
                the current checked-out reference if `revision` isn't an
                existing revision is allowed.
        """
        try:
            result = run_subprocess("git checkout".split() + [revision], self.local_dir)
            logger.warning(f"Checked out {revision} from {self.current_branch}.")
            logger.warning(result.stdout)
        except subprocess.CalledProcessError as exc:
            if not create_branch_ok:
                raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc
            else:
                try:
                    result = run_subprocess("git checkout -b".split() + [revision], self.local_dir)
                    logger.warning(
                        f"Revision `{revision}` does not exist. Created and checked out branch `{revision}`."
                    )
                    logger.warning(result.stdout)
                except subprocess.CalledProcessError as e:
                    raise EnvironmentError(replace_invalid_characters(exc.stderr)) from e

    def git_head_hash(self) -> str:
        """
        Get commit sha on top of HEAD.

        Returns:
            `str`: The current checked out commit SHA.
        """
        try:
            p = run_subprocess("git rev-parse HEAD", self.local_dir)
            return p.stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def git_remote_url(self) -> str:
        """
        Get URL to origin remote.

        Returns:
            `str`: The URL of the `origin` remote.
        """
        try:
            p = run_subprocess("git config --get remote.origin.url", self.local_dir)
            url = p.stdout.strip()
            # Strip basic auth info.
            return re.sub(r"https://.*@", "https://", url)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def git_head_commit_url(self) -> str:
        """
        Get URL to last commit on HEAD. We assume it's been pushed, and the url
        scheme is the same one as for GitHub or openMind.

        Returns:
            `str`: The URL to the current checked-out commit.
        """
        sha = self.git_head_hash()
        url = self.git_remote_url()
        if url.endswith("/"):
            url = url[:-1]
        return f"{url}/commit/{sha}"

    def list_deleted_files(self) -> List[str]:
        """
        Returns a list of the files that are deleted in the working directory or
        index.

        Returns:
            `List[str]`: A list of files that have been deleted in the working
            directory or index.
        """
        try:
            git_status = run_subprocess("git status -s", self.local_dir).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

        if not git_status:
            return []

        # Receives a status like the following
        #  D .gitignore
        #  D new_file.json
        # AD new_file1.json
        # ?? new_file2.json
        # ?? new_file4.json

        # Strip each line of whitespaces
        modified_files_statuses = [status.strip() for status in git_status.split("\n")]

        # Only keep files that are deleted using the D prefix
        deleted_files_statuses = [status for status in modified_files_statuses if "D" in status.split()[0]]

        # Remove the D prefix and strip to keep only the relevant filename
        deleted_files = [status.split()[-1].strip() for status in deleted_files_statuses]

        return deleted_files

    def lfs_track(self, patterns: Union[str, List[str]], filename: bool = False):
        """
        Tell git-lfs to track files according to a pattern.

        Setting the `filename` argument to `True` will treat the arguments as
        literal filenames, not as patterns. Any special glob characters in the
        filename will be escaped when writing to the `.gitattributes` file.

        Args:
            patterns (`Union[str, List[str]]`):
                The pattern, or list of patterns, to track with git-lfs.
            filename (`bool`, *optional*, defaults to `False`):
                Whether to use the patterns as literal filenames.
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        try:
            for pattern in patterns:
                if filename:
                    run_subprocess(
                        "git lfs track --filename".split() + [pattern],
                        self.local_dir,
                    )
                else:
                    run_subprocess(
                        "git lfs track".split() + [pattern],
                        self.local_dir,
                    )
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def lfs_untrack(self, patterns: Union[str, List[str]]):
        """
        Tell git-lfs to untrack those files.

        Args:
            patterns (`Union[str, List[str]]`):
                The pattern, or list of patterns, to untrack with git-lfs.
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        try:
            for pattern in patterns:
                run_subprocess("git lfs untrack".split() + [pattern], self.local_dir)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def auto_track_binary_files(self, pattern: str = ".") -> List[str]:
        """
        Automatically track binary files with git-lfs.

        Args:
            pattern (`str`, *optional*, defaults to "."):
                The pattern with which to track files that are binary.

        Returns:
            `List[str]`: List of filenames that are now tracked due to being
            binary files
        """
        files_to_be_tracked_with_lfs = []

        deleted_files = self.list_deleted_files()

        for filename in files_to_be_staged(pattern, folder=self.local_dir):
            if filename in deleted_files:
                continue

            path_to_file = os.path.join(os.getcwd(), self.local_dir, filename)

            if not (is_tracked_with_lfs(path_to_file) or is_git_ignored(path_to_file)):
                size_in_mb = os.path.getsize(path_to_file) / ONE_MEGABYTE

                if size_in_mb >= 10:
                    logger.warning(
                        "Parsing a large file to check if binary or not. Tracking large"
                        " files using `repository.auto_track_large_files` is"
                        " recommended so as to not load the full file in memory."
                    )

                is_binary = is_binary_file(path_to_file)

                if is_binary:
                    self.lfs_track(filename)
                    files_to_be_tracked_with_lfs.append(filename)

        # Cleanup the .gitattributes if files were deleted
        self.lfs_untrack(deleted_files)

        return files_to_be_tracked_with_lfs

    def auto_track_large_files(self, pattern: str = ".") -> List[str]:
        """
        Automatically track large files (files that weigh more than 10MBs) with
        git-lfs.

        Args:
            pattern (`str`, *optional*, defaults to "."):
                The pattern with which to track files that are above 10MBs.

        Returns:
            `List[str]`: List of filenames that are now tracked due to their
            size.
        """
        files_to_be_tracked_with_lfs = []

        deleted_files = self.list_deleted_files()

        for filename in files_to_be_staged(pattern, folder=self.local_dir):
            if filename in deleted_files:
                continue

            path_to_file = os.path.join(os.getcwd(), self.local_dir, filename)
            size_in_mb = os.path.getsize(path_to_file) / ONE_MEGABYTE

            if size_in_mb >= 10 and not is_tracked_with_lfs(path_to_file) and not is_git_ignored(path_to_file):
                self.lfs_track(filename)
                files_to_be_tracked_with_lfs.append(filename)

        # Cleanup the .gitattributes if files were deleted
        self.lfs_untrack(deleted_files)

        return files_to_be_tracked_with_lfs

    def lfs_prune(self, recent=False):
        """
        git lfs prune

        Args:
            recent (`bool`, *optional*, defaults to `False`):
                Whether to prune files even if they were referenced by recent
                commits. See the following
                [link](https://github.com/git-lfs/git-lfs/blob
                /f3d43f0428a84fc4f1e5405b76b5a73ec2437e65/docs/man
                /git-lfs-prune.1.ronn#recent-files)
                for more information.
        """
        try:
            with _lfs_log_progress():
                result = run_subprocess(f"git lfs prune {'--recent' if recent else ''}", self.local_dir)
                logger.info(result.stdout)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def git_add(self, pattern: str = ".", auto_lfs_track: bool = False):
        """
        git add

        Setting the `auto_lfs_track` parameter to `True` will automatically
        track files that are larger than 10MB with `git-lfs`.

        Args:
            pattern (`str`, *optional*, defaults to "."):
                The pattern with which to add files to staging.
            auto_lfs_track (`bool`, *optional*, defaults to `False`):
                Whether to automatically track large and binary files with
                git-lfs. Any file over 10MB in size, or in binary format, will
                be automatically tracked.
        """
        if auto_lfs_track:
            # Track files according to their size (>=10MB)
            tracked_files = self.auto_track_large_files(pattern)

            # Read the remaining files and track them if they're binary
            tracked_files.extend(self.auto_track_binary_files(pattern))

            if tracked_files:
                logger.warning(
                    f"Adding files tracked by Git LFS: {tracked_files}. This may take a"
                    " bit of time if the files are large."
                )

        try:
            result = run_subprocess("git add -v".split() + [pattern], self.local_dir)
            logger.info(f"Adding to index:\n{result.stdout}\n")
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def git_commit(self, commit_message: str = "commit files to hub"):
        """
        git commit

        Args:
            commit_message (`str`, *optional*, defaults to "commit files to hub"):
                The message attributed to the commit.
        """
        try:
            result = run_subprocess("git commit -v -m".split() + [commit_message], self.local_dir)
            logger.info(f"Committed:\n{result.stdout}\n")
        except subprocess.CalledProcessError as exc:
            if replace_invalid_characters(exc.stderr):
                raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc
            else:
                raise EnvironmentError(replace_invalid_characters(exc.stdout)) from exc

    def git_push(
        self,
        upstream: Optional[str] = None,
        blocking: bool = True,
        auto_lfs_prune: bool = False,
    ) -> Union[str, Tuple[str, CommandInProgress]]:
        """
        git push

        If used without setting `blocking`, will return url to commit on remote
        repo. If used with `blocking=T`, will return a tuple containing the
        url to commit and the command object to follow for information about the
        process.

        Args:
            upstream (`str`, *optional*):
                Upstream to which this should push. If not specified, will push
                to the lastly defined upstream or to the default one (`origin
                main`).
            blocking (`bool`, *optional*, defaults to `True`):
                Whether the function should return only when the push has
                finished. Setting this to `False` will return an
                `CommandInProgress` object which has an `is_done` property. This
                property will be set to `True` when the push is finished.
            auto_lfs_prune (`bool`, *optional*, defaults to `False`):
                Whether to automatically prune files once they have been pushed
                to the remote.
        """
        if urlparse(upstream).scheme:
            validate_url(upstream)
        command = "git push"

        if upstream:
            command += f" --set-upstream {upstream}"

        try:
            with _lfs_log_progress():
                process = Popen(
                    command.split(),
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    encoding="utf-8",
                    cwd=self.local_dir,
                    shell=False,
                )

                if blocking:
                    stdout, stderr = process.communicate(timeout=HUB_GIT_PUSH_TIMEOUT)
                    return_code = process.poll()
                    process.kill()

                    if len(stderr):
                        logger.warning(stderr)

                    if return_code:
                        raise subprocess.CalledProcessError(return_code, process.args, output=stdout, stderr=stderr)

        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from None

        if not blocking:

            def status_method():
                status = process.poll()
                if not status:
                    return -1
                else:
                    return status

            command_in_progress = CommandInProgress(
                "push",
                is_done_method=lambda: process.poll() is not None,
                status_method=status_method,
                process=process,
                post_method=self.lfs_prune if auto_lfs_prune else None,
            )

            self.command_queue.append(command_in_progress)

            return self.git_head_commit_url(), command_in_progress

        if auto_lfs_prune:
            self.lfs_prune()

        return self.git_head_commit_url()

    def git_pull(self, rebase: bool = False, lfs: bool = False):
        """
        git pull

        Args:
            rebase (`bool`, *optional*, defaults to `False`):
                Whether to rebase the current branch on top of the upstream
                branch after fetching.
            lfs (`bool`, *optional*, defaults to `False`):
                Whether to fetch the LFS files too. This option only changes the
                behavior when a repository was cloned without fetching the LFS
                files; calling `repo.git_pull(lfs=True)` will then fetch the LFS
                file from the remote repository.
        """
        command = "git pull" if not lfs else "git lfs pull"
        if rebase:
            command += " --rebase"
        try:
            with _lfs_log_progress():
                result = run_subprocess(command, self.local_dir)
                logger.info(result.stdout)
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

    def is_repo_clean(self) -> bool:
        """
        Return whether the git status is clean.

        Returns:
            `bool`: `True` if the git status is clean, `False` otherwise.
        """
        try:
            git_status = run_subprocess("git status --porcelain", self.local_dir).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise EnvironmentError(replace_invalid_characters(exc.stderr)) from exc

        return len(git_status) == 0

    def push_to_hub(
        self,
        commit_message: str = "End of training",
        blocking: bool = True,
        clean_ok: bool = True,
        auto_lfs_prune: bool = False,
    ) -> Union[None, str, Tuple[str, CommandInProgress]]:
        """
        Helper to add, commit, and push files to remote repository on the
        Model Foundry Hub. Will automatically track large files (>10MB).

        Args:
            commit_message (`str`):
                Message to use for the commit.
            blocking (`bool`, *optional*, defaults to `True`):
                Whether the function should return only when the `git push` has
                finished.
            clean_ok (`bool`, *optional*, defaults to `True`):
                If True, this function will return None if the repo is
                untouched. Default behavior is to fail because the git command
                fails.
            auto_lfs_prune (`bool`, *optional*, defaults to `False`):
                Whether to automatically prune files once they have been pushed
                to the remote.
        """
        if clean_ok and self.is_repo_clean():
            logger.info("Repo currently clean. Ignoring push_to_hub")
            return None
        self.git_add(auto_lfs_track=True)
        self.git_commit(commit_message)
        return self.git_push(
            upstream=f"origin {self.current_branch}",
            blocking=blocking,
            auto_lfs_prune=auto_lfs_prune,
        )

    def wait_for_commands(self):
        """
        Blocking method: blocks all subsequent execution until all commands have
        been processed.
        """
        index = 0
        for command_failed in self.commands_failed:
            logger.error(f"The {command_failed.title} command with PID {command_failed.get_process().pid} failed.")
            logger.error(command_failed.stderr)

        while self.commands_in_progress:
            if index % 10 == 0:
                logger.warning(
                    f"Waiting for the following commands to finish before shutting down: {self.commands_in_progress}."
                )

            index += 1

            time.sleep(1)
