"""
Internal rules for the bound project shell.

Ownership:
- This object owns one persistent interactive shell process scoped to a project
  working directory.
- This object owns shell-state guards such as cwd re-entry and SSH key loading.
- This object does not own git command semantics, repository-path resolution, or
  higher-level runtime/workflow policy.

Rule-set split:
- Internal method rules apply to raw shell-state helpers used to preserve the
  shell's intended execution contract.
- Encapsulated/public method rules apply to the exposed shell methods consumed by
  repository transport and bootstrap helpers.

Internal method rules:
- `_run_raw(...)` is the only method that may execute without first adding the
  normal shell-state guards.
- Internal shell-state helpers may call `_run_raw(...)` when they are themselves
  responsible for restoring the required shell state.
- Shell-state helpers must keep state restoration and command execution as
  distinct visible steps.

Encapsulated/public method rules:
- `run(...)` is the default command-execution entrypoint and must restore cwd
  through `ensure_working_directory()` before delegating to `_run_raw(...)`.
- `ensure_working_directory()` is the cwd guard for persistent-shell callers and
  should be treated as part of the shell execution contract.
- `ensure_ssh_key_loaded(...)` may rely on `run(...)` so SSH agent work occurs
  under the same cwd-restoring execution path as other shell-backed behavior.
- Callers should not bypass `run(...)` with `_run_raw(...)` unless they are
  implementing shell-state guards inside this file.
"""

import shlex
import subprocess


class ProjectShell:
    """Own one interactive shell process scoped to a project working directory."""

    def __init__(self, shell: str = "/bin/bash", working_directory: str | None = None):
        """Start the bound shell process used by repository transport work.

        Args:
            shell: Shell executable path to launch for command execution.
            working_directory: Optional working directory for the shell process.

        Returns:
            None: The shell process is started and stored on the instance.
        """
        self.key_loaded = False
        self.loaded_key_path: str | None = None
        self.working_directory = str(working_directory).strip() if working_directory is not None else None
        self.proc = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.working_directory,
        )

    def _run_raw(self, command: str) -> tuple[int, str]:
        """Run one command without adding shell-state guards.

        Args:
            command: Shell command string to execute in the running process.

        Returns:
            tuple[int, str]: Command return code and captured output text.
        """
        if not self.proc or self.proc.poll() is not None:
            raise ProjectShellError("Project shell is not running")

        marker = "__SHELL_DONE__"
        self.proc.stdin.write(f"{command}\necho {marker}:$?\n")
        self.proc.stdin.flush()

        output: list[str] = []
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break

            line = line.rstrip("\n")
            if line.startswith(marker):
                return_code = int(line.split(":")[-1])
                return return_code, "\n".join(output)

            output.append(line)

        raise ProjectShellError("Project shell ended unexpectedly")

    def ensure_working_directory(self) -> bool:
        """Ensure the bound shell is positioned at its configured working directory.

        Args:
            None.

        Returns:
            bool: `True` when the shell is already scoped or was re-scoped.
        """
        if self.working_directory is None:
            return True

        code, output = self._run_raw(f"cd {shlex.quote(self.working_directory)}")
        if code != 0:
            raise ProjectShellError(output.strip() or "Failed to enter configured working directory")

        return True

    def run(self, command: str):
        """Run one command inside the bound shell and capture combined output.

        Args:
            command: Shell command string to execute in the running process.

        Returns:
            tuple[int, str]: Command return code and captured output text.
        """
        self.ensure_working_directory()
        return self._run_raw(command)

    def ensure_ssh_key_loaded(self, key_path: str):
        """Ensure the requested SSH key is loaded into the shell agent session.

        Args:
            key_path: Filesystem path to the SSH private key to load.

        Returns:
            bool: `True` when the key is loaded or was already loaded.
        """
        normalized_key_path = str(key_path).strip()
        if not normalized_key_path:
            raise ProjectShellError("key_path is required")

        if self.key_loaded and self.loaded_key_path == normalized_key_path:
            return True

        code, output = self.run('eval "$(ssh-agent -s)"')
        if code != 0:
            raise ProjectShellError(output.strip() or "Failed to load ssh agent")

        code, output = self.run(f"ssh-add {normalized_key_path!r}")
        if code != 0:
            raise ProjectShellError(output.strip() or "Failed to load ssh key into agent")

        self.key_loaded = True
        self.loaded_key_path = normalized_key_path
        return True

    def close(self):
        """Close the bound shell process and reset key-loading state.

        Args:
            None.

        Returns:
            None: The shell is terminated and internal state is cleared.
        """
        if self.proc and self.proc.poll() is None:
            self.proc.stdin.write("exit\n")
            self.proc.stdin.flush()
            self.proc.wait()

        self.key_loaded = False
        self.loaded_key_path = None
        self.proc = None




class ProjectShellError(Exception):
    """Raised when the bound project shell cannot execute requested work."""

    pass
