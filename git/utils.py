import shlex
import subprocess
from errors import GitHubError


class PersistentShell:
    def __init__(self, shell="/bin/bash"):
        self.proc = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def run(self, command: str):
        if not self.proc or self.proc.poll() is not None:
            raise GitHubError(message="Persistent shell is not running")

        marker = "__SHELL_DONE__"
        self.proc.stdin.write(f"{command}\necho {marker}:$?\n")
        self.proc.stdin.flush()

        output = []
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break

            line = line.rstrip("\n")
            if line.startswith(marker):
                return_code = int(line.split(":")[-1])
                return return_code, "\n".join(output)

            output.append(line)

        raise GitHubError(message="Persistent shell ended unexpectedly")

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.stdin.write("exit\n")
            self.proc.stdin.flush()
            self.proc.wait()
        self.proc = None


class GitHub:
    def __init__(self, remote_repo_url, local_key_path, local_repo_path, branch="main"):
        self.remote_repo = remote_repo_url
        self.local_repo_path = local_repo_path
        self.key_path = local_key_path
        self.branch = branch
        self.shell = None
        self.key_loaded = False

    def start_shell(self):
        if self.shell is None:
            self.shell = PersistentShell()

    def _stop_shell(self):
        if self.shell:
            self.shell.close()
            self.shell = None
        self.key_loaded = False

    def _ensure_shell(self):
        self.start_shell()
        return self.shell

    def _ensure_key_loaded(self):
        if self.key_loaded:
            return True

        shell = self._ensure_shell()

        code, output = shell.run('eval "$(ssh-agent -s)"')
        if code != 0:
            raise GitHubError(message=f"Failed to load ssh agent. {output}")

        code, output = shell.run(f'ssh-add "{self.key_path}"')
        if code != 0:
            raise GitHubError(message=f"Failed to load ssh key into agent. {output}")

        self.key_loaded = True
        return True

    def _quote_args(self, args):
        return " ".join(shlex.quote(str(arg)) for arg in args)

    def run_git(self, args, require_key=False):
        try:
            shell = self._ensure_shell()

            if require_key:
                self._ensure_key_loaded()

            git_parts = ["git", "-C", self.local_repo_path, *args]
            git_command = self._quote_args(git_parts)

            code, output = shell.run(git_command)
            if code != 0:
                raise GitHubError(message=output.strip() or f"Git command failed with code {code}")

            return output.strip()
        except GitHubError:
            raise
        except Exception as e:
            raise GitHubError(message=str(e))

    def git_pull(self):
        return self.run_git(["pull", "origin", self.branch], require_key=True)

    def git_push(self):
        return self.run_git(["push", "origin", self.branch], require_key=True)

    def git_add(self, files="."):
        if isinstance(files, str):
            files = [files]
        elif not files:
            files = ["."]
        return self.run_git(["add", *files])

    def git_commit(self, message="+"):
        return self.run_git(["commit", "-m", message])

    def clone_repo(self, repo_path=None):
        target_path = repo_path or self.local_repo_path
        try:
            shell = self._ensure_shell()
            self._ensure_key_loaded()

            clone_parts = ["git", "clone", self.remote_repo, target_path]
            clone_command = self._quote_args(clone_parts)

            code, output = shell.run(clone_command)
            if code != 0:
                raise GitHubError(message=output.strip() or "Failed to clone repository")

            return output.strip()
        except GitHubError:
            raise
        except Exception as e:
            raise GitHubError(message=str(e))

    def close(self):
        self._stop_shell()