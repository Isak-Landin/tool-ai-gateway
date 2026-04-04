"""
Shared bootstrap-local shell command helpers.
"""

import shlex

from errors import ProjectBootstrapError
from repository_runtime.shell import ProjectShell


def _quote_args(command_args: list[str]) -> str:
    return " ".join(shlex.quote(str(command_arg)) for command_arg in command_args)


def _require_shell(shell: ProjectShell | None) -> ProjectShell:
    if shell is None:
        raise ProjectBootstrapError(
            "shell is required for shell-backed bootstrap work",
            field="shell",
            error_type="missing dependency",
            file_id=__file__,
        )

    return shell


def _run_command(
    shell: ProjectShell | None,
    command_args: list[str],
) -> tuple[int, str]:
    required_shell = _require_shell(shell)
    required_shell.ensure_working_directory()
    command_text = _quote_args(command_args)
    command_return_code, command_output = required_shell.run(command_text)
    return int(command_return_code), command_output.strip()


def _run_command_return_output(
    shell: ProjectShell | None,
    command_args: list[str],
    *,
    failure_message: str = "",
    field: str = "",
    error_type: str = "",
) -> str:
    command_return_code, command_output = _run_command(
        shell=shell,
        command_args=command_args,
    )
    if command_return_code != 0:
        raise ProjectBootstrapError(
            command_output or failure_message,
            field=field,
            error_type=error_type,
            file_id=__file__,
        )

    return command_output
