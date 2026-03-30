import subprocess


class ProjectShellError(Exception):
    """Raised when the bound project shell cannot execute requested work."""

    pass


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
        self.proc = subprocess.Popen(
            [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=working_directory,
        )

    def run(self, command: str):
        """Run one command inside the bound shell and capture combined output.

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
