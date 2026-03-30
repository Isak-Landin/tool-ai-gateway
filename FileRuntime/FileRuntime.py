from __future__ import annotations

from pathlib import PurePosixPath

from errors import FileRuntimeError, RepositoryFilePersistenceError
from repository_tools import (
    get_repository_ignore_patterns,
    is_ignored_repository_path,
    normalize_repository_relative_path,
    quote_shell_args,
)


class FileRuntime:
    """
    Project-bound live file/tree runtime surface.

    This object owns project-scoped live repository reads for file/tree consumers.
    It may also reuse persistence-shaped file storage when explicitly requested,
    but it does not turn file persistence into the live serving owner.
    """

    def __init__(
        self,
        *,
        project_id: int,
        repo_path: str,
        branch: str,
        repository_runtime,
        files_repository=None,
    ):
        """Create the bound live file runtime for one project and branch.

        Args:
            project_id: Persisted project identifier that scopes runtime behavior.
            repo_path: Local repository path used for live git-backed reads.
            branch: Effective branch value for live file/tree/search operations.
            repository_runtime: Bound repository transport runtime used underneath file access.
            files_repository: Optional storage-shaped file repository for snapshot persistence.

        Returns:
            None: The runtime stores project scope, transport, and optional storage access.
        """
        if project_id is None:
            raise FileRuntimeError("project_id is required")
        if not str(repo_path).strip():
            raise FileRuntimeError("repo_path is required")
        if repository_runtime is None:
            raise FileRuntimeError("repository_runtime is required")

        self.project_id = project_id
        self.repo_path = str(repo_path).strip()
        self.branch = str(branch or "main").strip()
        self._repository_runtime = repository_runtime
        self._files_repository = files_repository
        self._resolved_branch_reference: str | None = None
        self._ignore_patterns: list[str] | None = None

    @property
    def repository_runtime(self):
        """Reject direct unwrapping back to repository transport.

        Args:
            None.

        Returns:
            Never: This property always raises to keep callers on FileRuntime.
        """
        raise FileRuntimeError(
            "Direct FileRuntime.repository_runtime access is deprecated; FileRuntime should serve live file/tree access "
            "without callers unwrapping RepositoryRuntime"
        )

    def _require_files_repository(self):
        """Return the storage-shaped file repository or fail when it is missing.

        Args:
            None.

        Returns:
            Any: File-row persistence dependency used for snapshot operations.
        """
        if self._files_repository is None:
            raise FileRuntimeError("files_repository is required for persistence-backed file operations")

        return self._files_repository

    def _run_git_command(self, args: list[str], *, allowed_return_codes: set[int] | None = None) -> str:
        """Run one git command through the bound repository shell.

        Args:
            args: Git command arguments without the leading `git`.
            allowed_return_codes: Optional set of acceptable process return codes.

        Returns:
            str: Captured git command output text.
        """
        allowed_codes = allowed_return_codes or {0}
        command = quote_shell_args(["git", *args])
        return_code, output = self._repository_runtime.shell.run(command)
        if return_code not in allowed_codes:
            raise FileRuntimeError(output.strip() or f"git command failed with code {return_code}")
        return output

    def _resolve_branch_reference(self) -> str:
        """Resolve the git branch reference that should back live reads.

        Args:
            None.

        Returns:
            str: Verified git branch reference that can be used in commands.
        """
        if self._resolved_branch_reference is not None:
            return self._resolved_branch_reference

        branch_candidates: list[str] = []
        normalized_branch = str(self.branch or "").strip()
        if normalized_branch:
            branch_candidates.append(normalized_branch)
            if not normalized_branch.startswith("origin/"):
                branch_candidates.append(f"origin/{normalized_branch}")

        seen_candidates: set[str] = set()
        for branch_candidate in branch_candidates:
            if branch_candidate in seen_candidates:
                continue
            seen_candidates.add(branch_candidate)

            return_code, _ = self._repository_runtime.shell.run(
                quote_shell_args(["git", "rev-parse", "--verify", f"{branch_candidate}^{{commit}}"])
            )
            if return_code == 0:
                self._resolved_branch_reference = branch_candidate
                return branch_candidate

        raise FileRuntimeError(f"Repository branch reference is not available: {self.branch}")

    def _get_ignore_patterns(self) -> list[str]:
        """Load and cache the configured repository ignore patterns.

        Args:
            None.

        Returns:
            list[str]: Cached ignore-pattern strings used by live file operations.
        """
        if self._ignore_patterns is None:
            self._ignore_patterns = get_repository_ignore_patterns()
        return list(self._ignore_patterns)

    def get_ignore_patterns(self) -> list[str]:
        """Expose the configured repository ignore patterns for this runtime.

        Args:
            None.

        Returns:
            list[str]: Configured ignore-pattern strings used by live reads.
        """
        return self._get_ignore_patterns()

    def _normalize_relative_repo_path(self, relative_repo_path: str | None = None, *, allow_root: bool) -> str:
        """Normalize a repo-relative path for live runtime operations.

        Args:
            relative_repo_path: Optional repo-relative path provided by the caller.
            allow_root: Whether the repository root path `/` is allowed.

        Returns:
            str: Normalized repo-relative path suitable for runtime use.
        """
        try:
            return normalize_repository_relative_path(relative_repo_path, allow_root=allow_root)
        except ValueError as e:
            raise FileRuntimeError(str(e)) from e

    def _assert_not_ignored(self, normalized_relative_path: str) -> None:
        """Fail when a normalized path is excluded by configured ignore rules.

        Args:
            normalized_relative_path: Normalized repo-relative path to validate.

        Returns:
            None: Validation succeeds silently or raises a file-runtime error.
        """
        if is_ignored_repository_path(normalized_relative_path, self._get_ignore_patterns()):
            raise FileRuntimeError(f"Path is excluded by configured ignore paths: {normalized_relative_path}")

    def _get_branch_entry_type(self, normalized_relative_path: str) -> str:
        """Look up whether a branch path is a tree, blob, or missing entry.

        Args:
            normalized_relative_path: Normalized repo-relative path to inspect.

        Returns:
            str: Git entry type such as `tree` or `blob` for the requested path.
        """
        if normalized_relative_path == "/":
            return "tree"

        branch_reference = self._resolve_branch_reference()
        git_relative_path = normalized_relative_path.lstrip("/")
        output = self._run_git_command(
            ["ls-tree", branch_reference, "--", git_relative_path],
            allowed_return_codes={0},
        )

        for output_line in output.splitlines():
            metadata, separator, path_part = output_line.partition("\t")
            if not separator or path_part != git_relative_path:
                continue

            metadata_parts = metadata.split()
            if len(metadata_parts) >= 2:
                return metadata_parts[1]

        raise FileRuntimeError(f"Path does not exist in branch {self.branch}: {normalized_relative_path}")

    def _build_tree_entry(self, normalized_relative_path: str, base_relative_path: str, *, is_dir: bool) -> dict:
        """Build the serialized tree-entry payload for one file or directory.

        Args:
            normalized_relative_path: Normalized full repo-relative path for the entry.
            base_relative_path: Normalized repo-relative path used as the listing base.
            is_dir: Whether the serialized entry should be marked as a directory.

        Returns:
            dict: Tree-entry payload with path, name, type flags, and relative depth.
        """
        if base_relative_path == "/":
            relative_parts = PurePosixPath(normalized_relative_path.lstrip("/")).parts
        else:
            relative_parts = PurePosixPath(normalized_relative_path.lstrip("/")).relative_to(
                PurePosixPath(base_relative_path.lstrip("/"))
            ).parts

        return {
            "name": PurePosixPath(normalized_relative_path.lstrip("/")).name,
            "path": normalized_relative_path,
            "is_dir": is_dir,
            "is_file": not is_dir,
            "depth": len(relative_parts),
        }

    def load_selected_context(self, selected_files: list[str]) -> list[dict]:
        """Load live selected-file context rows for execution use.

        Args:
            selected_files: Repo-relative file paths selected for the current run.

        Returns:
            list[dict]: Minimal file-context rows with name, path, and content.
        """
        selected_paths = [str(selected_file).strip() for selected_file in selected_files if str(selected_file).strip()]
        if not selected_paths:
            return []

        selected_context_rows: list[dict] = []
        for selected_path in selected_paths:
            live_file = self.read_file(relative_repo_path=selected_path)
            selected_context_rows.append(
                {
                    "name": live_file["name"],
                    "path": live_file["path"],
                    "content": live_file["content"],
                }
            )

        return selected_context_rows

    def list_tree(self, relative_repo_path: str | None = None) -> list[dict]:
        """List live repository tree entries for a repo-relative directory path.

        Args:
            relative_repo_path: Optional repo-relative directory path to list from.

        Returns:
            list[dict]: Tree-entry payloads describing files and directories.
        """
        normalized_relative_path = self._normalize_relative_repo_path(relative_repo_path, allow_root=True)
        self._assert_not_ignored(normalized_relative_path)

        if self._get_branch_entry_type(normalized_relative_path) != "tree":
            raise FileRuntimeError(f"Path is not a directory in branch {self.branch}: {normalized_relative_path}")

        branch_reference = self._resolve_branch_reference()
        git_relative_path = normalized_relative_path.lstrip("/")
        git_args = ["ls-tree", "-r", "--name-only", branch_reference]
        if git_relative_path:
            git_args.extend(["--", git_relative_path])

        output = self._run_git_command(git_args, allowed_return_codes={0})

        directory_paths: set[str] = set()
        file_paths: list[str] = []
        base_parts = PurePosixPath(git_relative_path).parts if git_relative_path else ()

        for output_line in output.splitlines():
            normalized_output_line = output_line.strip()
            if not normalized_output_line:
                continue

            normalized_file_path = "/" + normalized_output_line.lstrip("/")
            if is_ignored_repository_path(normalized_file_path, self._get_ignore_patterns()):
                continue

            file_paths.append(normalized_file_path)

            relative_file_parts = (
                PurePosixPath(normalized_file_path.lstrip("/")).parts
                if normalized_relative_path == "/"
                else PurePosixPath(normalized_file_path.lstrip("/")).relative_to(PurePosixPath(git_relative_path)).parts
            )

            for depth_index in range(1, len(relative_file_parts)):
                directory_parts = (*base_parts, *relative_file_parts[:depth_index])
                directory_path = "/" + "/".join(directory_parts)
                if is_ignored_repository_path(directory_path, self._get_ignore_patterns()):
                    continue
                directory_paths.add(directory_path)

        tree_entries: list[dict] = []
        for directory_path in sorted(directory_paths):
            tree_entries.append(
                self._build_tree_entry(
                    directory_path,
                    normalized_relative_path,
                    is_dir=True,
                )
            )

        for file_path in sorted(file_paths):
            tree_entries.append(
                self._build_tree_entry(
                    file_path,
                    normalized_relative_path,
                    is_dir=False,
                )
            )

        return tree_entries

    def read_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        """Read live file content for a repo-relative path and optional line range.

        Args:
            relative_repo_path: Repo-relative file path to read from the active branch.
            start_line: Optional first line number to include.
            number_of_lines: Optional count of lines to include from `start_line`.
            end_line: Optional inclusive last line number to include.

        Returns:
            dict: File payload including content, path, and line-range metadata.
        """
        if number_of_lines is not None and end_line is not None:
            raise FileRuntimeError("Use either number_of_lines or end_line, not both")

        normalized_relative_path = self._normalize_relative_repo_path(relative_repo_path, allow_root=False)
        self._assert_not_ignored(normalized_relative_path)

        if self._get_branch_entry_type(normalized_relative_path) != "blob":
            raise FileRuntimeError(f"Path is not a file in branch {self.branch}: {normalized_relative_path}")

        effective_start_line = 1 if start_line is None else start_line
        if effective_start_line < 1:
            raise FileRuntimeError("start_line must be >= 1")
        if number_of_lines is not None and number_of_lines < 1:
            raise FileRuntimeError("number_of_lines must be >= 1")
        if end_line is not None and end_line < effective_start_line:
            raise FileRuntimeError("end_line must be >= start_line")

        branch_reference = self._resolve_branch_reference()
        git_relative_path = normalized_relative_path.lstrip("/")
        file_content = self._run_git_command(
            ["show", f"{branch_reference}:{git_relative_path}"],
            allowed_return_codes={0},
        )

        all_lines = file_content.splitlines()
        total_lines = len(all_lines)
        if number_of_lines is not None:
            effective_end_line = effective_start_line + number_of_lines - 1
        elif end_line is not None:
            effective_end_line = end_line
        else:
            effective_end_line = total_lines

        effective_end_line = min(effective_end_line, total_lines)
        content_lines = all_lines[effective_start_line - 1:effective_end_line]

        return {
            "name": PurePosixPath(git_relative_path).name,
            "path": normalized_relative_path,
            "content": "\n".join(content_lines),
            "start_line": effective_start_line,
            "end_line": effective_end_line,
            "total_lines": total_lines,
        }

    def search_text(
        self,
        query: str,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        """Search live repository text for a query and optional path scope.

        Args:
            query: Search query text to match in repository files.
            relative_repo_path: Optional repo-relative path to limit the search scope.
            case_sensitive: Whether the search should preserve letter case.
            max_results: Maximum number of matches to include in the result list.

        Returns:
            list[dict]: Search-match payloads with path, line number, and line text.
        """
        if not str(query).strip():
            raise FileRuntimeError("query is required")
        if max_results < 1:
            raise FileRuntimeError("max_results must be >= 1")

        normalized_relative_path = self._normalize_relative_repo_path(relative_repo_path, allow_root=True)
        self._assert_not_ignored(normalized_relative_path)
        if normalized_relative_path != "/":
            self._get_branch_entry_type(normalized_relative_path)

        branch_reference = self._resolve_branch_reference()
        git_args = ["grep", "-n", "--full-name", "--color=never"]
        if not case_sensitive:
            git_args.append("-i")
        git_args.extend(["-e", query, branch_reference])

        git_relative_path = normalized_relative_path.lstrip("/")
        if git_relative_path:
            git_args.extend(["--", git_relative_path])

        output = self._run_git_command(git_args, allowed_return_codes={0, 1})

        search_results: list[dict] = []
        for output_line in output.splitlines():
            treeish_part, separator, remainder = output_line.partition(":")
            if not separator or treeish_part != branch_reference:
                continue

            path_part, separator, remainder = remainder.partition(":")
            if not separator:
                continue

            line_number_part, separator, line_text = remainder.partition(":")
            if not separator:
                continue

            normalized_result_path = "/" + path_part.lstrip("/")
            if is_ignored_repository_path(normalized_result_path, self._get_ignore_patterns()):
                continue

            try:
                line_number = int(line_number_part)
            except ValueError:
                continue

            search_results.append(
                {
                    "path": normalized_result_path,
                    "line_number": line_number,
                    "line_text": line_text,
                }
            )
            if len(search_results) >= max_results:
                break

        return search_results

    def list_persisted_files(self) -> list[dict]:
        """List persisted file snapshot rows for the configured project.

        Args:
            None.

        Returns:
            list[dict]: Serialized persisted file rows for this project.
        """
        files_repository = self._require_files_repository()
        try:
            return files_repository.list_file_rows()
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e

    def get_persisted_file(self, relative_repo_path: str) -> dict | None:
        """Load one persisted file snapshot by repo-relative path.

        Args:
            relative_repo_path: Repo-relative file path to look up in storage.

        Returns:
            dict | None: Serialized persisted file row when found, otherwise `None`.
        """
        files_repository = self._require_files_repository()
        try:
            return files_repository.get_file_row_by_path(relative_repo_path)
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e

    def persist_file_snapshot(self, relative_repo_path: str) -> dict:
        """Persist a fresh live file snapshot into storage for the current project.

        Args:
            relative_repo_path: Repo-relative file path to read live and persist.

        Returns:
            dict: Serialized persisted file row after snapshot storage completes.
        """
        live_file = self.read_file(relative_repo_path=relative_repo_path)
        files_repository = self._require_files_repository()
        try:
            return files_repository.upsert_file_row(
                relative_repo_path=live_file["path"],
                name=live_file["name"],
                content=live_file["content"],
                total_lines=live_file["total_lines"],
            )
        except RepositoryFilePersistenceError as e:
            raise FileRuntimeError(str(e)) from e
