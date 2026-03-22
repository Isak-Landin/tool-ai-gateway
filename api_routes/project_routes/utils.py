from api_routes.project_routes.schemas import ChatResponse, ChatRequest

# =========================================================
# INTERNAL WORKFLOW HELPERS
# =========================================================

def chat_workflow_entry(project_id, req: ChatRequest, resolver, binder, orchestrator) -> ChatResponse:
    """
    resolver = ProjectResolver()
    binder = ProjectBinder()
    orchestrator = WorkflowOrchestrator()
    """

    project_row = resolver.resolve_by_id(project_id)
    handle = binder.bind(project_row)

    result = orchestrator.run_chat(
        handle=handle,
        message=req.message,
        selected_files=req.selected_files,
    )

    return ChatResponse(
        ok=result.get("ok", False),
        project_id=project_id,
        message=result.get("answer", result.get("message", "")),
        selected_files=req.selected_files,
        next_layer="execution_completed",
    )