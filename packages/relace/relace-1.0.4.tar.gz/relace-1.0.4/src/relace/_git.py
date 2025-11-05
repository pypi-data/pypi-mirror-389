import shlex
import subprocess
from typing import TYPE_CHECKING, List, Union, Optional

if TYPE_CHECKING:
    from ._client import Relace


def ensure_git_available() -> None:
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        raise RuntimeError("Git CLI is not installed or not found in PATH.") from exc


class GitHelper:
    def __init__(self, client: "Relace", root_path: str) -> None:
        self.client = client
        self.root_path = root_path

    def clone(self, repo_id: str, depth: int = 1, branch: Optional[str] = None, quiet: bool = True, *args: str) -> None:
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        branch_arg = ["-b", branch] if branch else []
        quiet_arg = ["--quiet"] if quiet else []
        extra_args = list(args)

        api_token = self.client.api_key
        repo_url = f"https://token:{api_token}@api.relace.run/v1/repo/{repo_id}.git"

        ensure_git_available()
        cmd = ["git", "clone", "--depth", str(depth)] + branch_arg + quiet_arg + extra_args + [repo_url, self.root_path]

        subprocess.run(cmd, check=True)

    def add(self, files: Union[str, List[str]] = ".") -> "GitHelper":
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        files_arg = files if isinstance(files, str) else " ".join(files)

        ensure_git_available()
        subprocess.run(["git", "-C", self.root_path, "add"] + files_arg.split(), check=True)

        return self

    def commit(self, message: str) -> "GitHelper":
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        if not message:
            raise ValueError("Please specify a commit message")

        ensure_git_available()
        subprocess.run(["git", "-C", self.root_path, "commit", "-m", message], check=True)

        return self

    def push(self, branch: Optional[str] = None) -> None:
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        ensure_git_available()
        # Determine head branch if not provided
        if not branch:
            result = subprocess.run(
                ["git", "-C", self.root_path, "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            branch = result.stdout.strip()

        # Push with upstream
        subprocess.run(["git", "-C", self.root_path, "push", "-u", "origin", branch], check=True)

    def fetch(self, branch: Optional[str] = None) -> None:
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        ensure_git_available()

        cmd = ["git", "-C", self.root_path, "fetch"]
        if branch:
            cmd.extend(["origin", branch])

        subprocess.run(cmd, check=True)

    def pull(self, branch: Optional[str] = None) -> None:
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        ensure_git_available()

        cmd = ["git", "-C", self.root_path, "pull"]
        if branch:
            cmd.extend(["origin", branch])

        subprocess.run(cmd, check=True)

    def checkout_branch(self, branch: str, new_branch: bool = False) -> None:
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        ensure_git_available()
        cmd = ["git", "-C", self.root_path, "checkout"]

        if new_branch:
            cmd.append("-b")

        cmd.append(branch)

        subprocess.run(cmd, check=True)

    def command(self, cmd: str) -> "GitHelper":
        if not self.root_path:
            raise ValueError("No repository path provided. Please specify in git() parameter")

        if not cmd:
            raise ValueError("Please provide a Git command to execute.")

        ensure_git_available()

        # Use shlex.split to split the command string into a list of arguments
        full_cmd = ["git", "-C", self.root_path] + shlex.split(cmd)

        subprocess.run(full_cmd, check=True)
        return self


def attach_git_support() -> None:
    from ._client import Relace
    
    def git(self: "Relace", root_path: str) -> "GitHelper":
        return GitHelper(self, root_path)

    Relace.git = git  # type: ignore[method-assign]
