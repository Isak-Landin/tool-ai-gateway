import shutil
import subprocess
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.session import SessionLocal
from db.models import Project, File
from errors import PersistenceError






class FilesRepository:
    def __init__(self, db_connection=None, project_id: int | None = None, repo_path: str | None = None):
        self.db_connection = db_connection
        self.project_id = project_id
        self.repo_path = repo_path

    def _get_repo_root(self) -> Path:
        repo_path = self.repo_path

        if repo_path is None and self.project_id is not None:
            session = self.db_connection or SessionLocal()
            try:
                stmt = select(Project.repo_path).where(Project.project_id == self.project_id)
                repo_path = session.execute(stmt).scalar_one_or_none()
            except SQLAlchemyError as e:
                raise PersistenceError(str(e))
            finally:
                if self.db_connection is None:
                    session.close()

        if not repo_path:
            raise PersistenceError("repo_path is required for repository file access")

        repo_root = Path(repo_path).expanduser().resolve()
        if not repo_root.exists():
            raise PersistenceError(f"Repository path does not exist: {repo_root}")
        if not repo_root.is_dir():
            raise PersistenceError(f"Repository path is not a directory: {repo_root}")

        return repo_root

    def _resolve_repo_path(self, relative_repo_path: str | None = None) -> tuple[Path, Path]:
        repo_root = self._get_repo_root()

        normalized = (relative_repo_path or "").strip()
        if normalized in {"", ".", "/"}:
            target_path = repo_root
        else:
            target_path = (repo_root / normalized.lstrip("/")).resolve()

        try:
            target_path.relative_to(repo_root)
        except ValueError as e:
            raise PersistenceError(f"Path escapes repository root: {relative_repo_path}") from e

        if not target_path.exists():
            scoped_path = relative_repo_path or "/"
            raise PersistenceError(f"Path does not exist in repository: {scoped_path}")

        return repo_root, target_path

    def _relative_repo_string(self, repo_root: Path, target_path: Path) -> str:
        relative_path = target_path.relative_to(repo_root)
        if str(relative_path) == ".":
            return "/"

        return "/" + relative_path.as_posix()

    def _build_path_entry(self, repo_root: Path, target_path: Path) -> dict:
        return {
            "name": target_path.name or repo_root.name,
            "path": self._relative_repo_string(repo_root, target_path),
            "is_dir": target_path.is_dir(),
            "is_file": target_path.is_file(),
        }

    def list_by_project(self) -> list[dict]:
        session = self.db_connection or SessionLocal()
        try:
            stmt = select(File).where(File.project_id == self.project_id)
            rows = session.execute(stmt).scalars().all()

            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "content": r.content,
                    "project_id": r.project_id,
                }
                for r in rows
            ]

        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()

    def list_files(self, relative_repo_path: str | None = None) -> list[dict]:
        repo_root, target_path = self._resolve_repo_path(relative_repo_path)

        if not target_path.is_dir():
            raise PersistenceError(
                f"Path is not a directory in repository: {self._relative_repo_string(repo_root, target_path)}"
            )

        entries = sorted(
            target_path.iterdir(),
            key=lambda item: (not item.is_dir(), item.name.lower()),
        )

        return [self._build_path_entry(repo_root, entry) for entry in entries]

    def list_tree(self, relative_repo_path: str | None = None) -> list[dict]:
        repo_root, target_path = self._resolve_repo_path(relative_repo_path)

        if not target_path.is_dir():
            raise PersistenceError(
                f"Path is not a directory in repository: {self._relative_repo_string(repo_root, target_path)}"
            )

        entries = []
        for entry in sorted(target_path.rglob("*"), key=lambda item: item.as_posix().lower()):
            entries.append(
                {
                    **self._build_path_entry(repo_root, entry),
                    "depth": len(entry.relative_to(target_path).parts),
                }
            )

        return entries

    def read_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        if number_of_lines is not None and end_line is not None:
            raise PersistenceError("Use either number_of_lines or end_line, not both")

        repo_root, target_path = self._resolve_repo_path(relative_repo_path)
        if not target_path.is_file():
            raise PersistenceError(
                f"Path is not a file in repository: {self._relative_repo_string(repo_root, target_path)}"
            )

        if start_line is None:
            start_line = 1
        if start_line < 1:
            raise PersistenceError("start_line must be >= 1")
        if number_of_lines is not None and number_of_lines < 1:
            raise PersistenceError("number_of_lines must be >= 1")
        if end_line is not None and end_line < start_line:
            raise PersistenceError("end_line must be >= start_line")

        try:
            all_lines = target_path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            raise PersistenceError(str(e)) from e

        total_lines = len(all_lines)
        if number_of_lines is not None:
            effective_end_line = start_line + number_of_lines - 1
        elif end_line is not None:
            effective_end_line = end_line
        else:
            effective_end_line = total_lines

        effective_end_line = min(effective_end_line, total_lines)
        content_lines = all_lines[start_line - 1:effective_end_line]

        return {
            "name": target_path.name,
            "path": self._relative_repo_string(repo_root, target_path),
            "content": "\n".join(content_lines),
            "start_line": start_line,
            "end_line": effective_end_line,
            "total_lines": total_lines,
        }

    def search_in_files(
        self,
        query: str,
        files: list[str] | None = None,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        if not str(query).strip():
            raise PersistenceError("query is required")
        if max_results < 1:
            raise PersistenceError("max_results must be >= 1")

        repo_root, target_path = self._resolve_repo_path(relative_repo_path)

        search_targets: list[Path]
        if files:
            search_targets = []
            for file_path in files:
                _, resolved_path = self._resolve_repo_path(file_path)
                search_targets.append(resolved_path)
        else:
            search_targets = [target_path]

        rg_path = shutil.which("rg")
        if rg_path is None:
            raise PersistenceError("ripgrep (rg) is required for search_in_files")

        command = [
            rg_path,
            "--line-number",
            "--with-filename",
            "--color",
            "never",
        ]
        if not case_sensitive:
            command.append("-i")

        command.append(query)
        command.extend(str(path) for path in search_targets)

        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )

        if completed.returncode not in {0, 1}:
            raise PersistenceError(completed.stderr.strip() or completed.stdout.strip() or "ripgrep failed")

        results: list[dict] = []
        for line in completed.stdout.splitlines():
            path_part, separator, remainder = line.partition(":")
            if not separator:
                continue

            line_number_part, separator, line_text = remainder.partition(":")
            if not separator:
                continue

            result_path = Path(path_part).resolve()
            try:
                relative_result = "/" + result_path.relative_to(repo_root).as_posix()
            except ValueError:
                relative_result = path_part

            try:
                line_number = int(line_number_part)
            except ValueError:
                continue

            results.append(
                {
                    "path": relative_result,
                    "line_number": line_number,
                    "line_text": line_text,
                }
            )

            if len(results) >= max_results:
                break

        return results

    def search_files(self, query: str) -> list[dict]:
        return self.search_in_files(query=query)

    def get_file(
        self,
        relative_repo_path: str,
        start_line: int | None = None,
        number_of_lines: int | None = None,
        end_line: int | None = None,
    ) -> dict | None:
        return self.read_file(
            relative_repo_path=relative_repo_path,
            start_line=start_line,
            number_of_lines=number_of_lines,
            end_line=end_line,
        )
