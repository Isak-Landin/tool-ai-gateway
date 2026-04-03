from __future__ import annotations

from contextlib import contextmanager

from BoundProjectRuntime import BoundProjectRuntime
from ProjectResolver import ProjectResolver
from ProjectRuntimeBinder import ProjectRuntimeBinder
from execution import WorkflowOrchestrator


class RouteProjectRuntime:
    """Expose only route-safe bound runtime surfaces.

    This wrapper keeps route-facing code on the intended file owner instead of
    exposing the broader execution/runtime dependency bag.
    """

    def __init__(self, handle: BoundProjectRuntime):
        """Build a narrowed route runtime from a full bound project runtime.

        Args:
            handle: Bound runtime carrying the already-attached project dependencies.

        Returns:
            None: The route runtime stores narrowed references for later access.
        """
        self.project_id = handle.project_id
        self.branch = handle.branch

        self._repository_runtime = handle.require_repository_runtime()

    def require_repository_runtime(self):
        """Return the bound repository runtime for route-facing live file access.

        Args:
            None.

        Returns:
            Any: Bound repository runtime used by file-runtime functions.
        """
        return self._repository_runtime


@contextmanager
def bound_project_execution_runtime(project_id: int, *, branch_override: str | None = None):
    """Resolve and bind a full project runtime for execution-oriented callers.

    Args:
        project_id: Persisted project identifier to resolve and bind.
        branch_override: Optional branch value to use instead of the stored branch.

    Returns:
        Iterator[BoundProjectRuntime]: Context manager yielding the bound runtime handle.
    """
    resolver = ProjectResolver()
    binder = ProjectRuntimeBinder()
    project_row = resolver.resolve_by_id(project_id)
    handle = binder.bind(project_row, branch_override=branch_override)
    try:
        yield handle
    finally:
        if hasattr(handle, "close"):
            handle.close()


@contextmanager
def bound_project_route_runtime(project_id: int, *, branch_override: str | None = None):
    """Resolve and bind a narrowed route runtime for route-facing live reads.

    Args:
        project_id: Persisted project identifier to resolve and bind.
        branch_override: Optional branch value to use instead of the stored branch.

    Returns:
        Iterator[RouteProjectRuntime]: Context manager yielding the narrowed route runtime.
    """
    with bound_project_execution_runtime(project_id, branch_override=branch_override) as handle:
        yield RouteProjectRuntime(handle)


def build_workflow_orchestrator() -> WorkflowOrchestrator:
    """Create the workflow orchestrator used by chat-run routes.

    Args:
        None.

    Returns:
        WorkflowOrchestrator: Fresh orchestrator instance for execution work.
    """
    return WorkflowOrchestrator()
