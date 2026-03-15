from project_handle import ProjectHandle
from ollama.ollama_client import call_ollama, parse_model_output
from archon.archon import archon_search, archon_rag_query


class WorkflowExecutionError(Exception):
    pass


class WorkflowOrchestrator:

    def run_chat(self, handle: ProjectHandle, message: str, selected_files: list[str] | None = None) -> dict:

        if handle is None:
            raise WorkflowExecutionError("ProjectHandle is required")

        if not str(message).strip():
            raise WorkflowExecutionError("message is required")

        if selected_files is None:
            selected_files = []

        # STEP 1 — load history
        history_rows = handle.messages.list_by_project()

        history = []
        for m in history_rows:
            history.append({
                "role": m.get("role"),
                "content": m.get("content"),
            })

        # STEP 2 — load selected files
        file_rows = handle.files.list_by_project()

        selected_context = []
        if selected_files:
            for f in file_rows:
                if f.get("name") in selected_files:
                    if f.get("content"):
                        selected_context.append(f.get("content"))

        if selected_context:
            message = message + "\n\n" + "\n\n".join(selected_context)

        # sequence start
        sequence_no = len(history_rows) + 1

        # STEP 3 — call model
        response = call_ollama(message, history)

        # STEP 4 — parse response
        result = parse_model_output(response)

        tool_result = None

        # STEP 5 — tool dispatch
        if result.get("action") == "tool":

            tool_name = result.get("tool_name")
            args = result.get("arguments") or {}

            if tool_name == "archon_search":
                tool_result = archon_search(**args)

            elif tool_name == "archon_rag_query":
                tool_result = archon_rag_query(**args)

            else:
                raise WorkflowExecutionError(f"Unknown tool: {tool_name}")

            tool_history = history + [
                {"role": "user", "content": message},
                {"role": "tool", "content": str(tool_result)},
            ]

            response = call_ollama(message, tool_history)
            result = parse_model_output(response)

        # STEP 6 — persist user message
        handle.messages.insert_message({
            "project_id": handle.project_id,
            "sequence_no": sequence_no,
            "role": "user",
            "content": message,
        })

        sequence_no += 1

        # persist tool message if used
        if tool_result is not None:
            handle.messages.insert_message({
                "project_id": handle.project_id,
                "sequence_no": sequence_no,
                "role": "tool",
                "content": str(tool_result),
            })
            sequence_no += 1

        assistant_answer = result.get("answer", "")

        # persist assistant message
        handle.messages.insert_message({
            "project_id": handle.project_id,
            "sequence_no": sequence_no,
            "role": "assistant",
            "content": assistant_answer,
        })

        return {
            "ok": True,
            "execution_type": "chat",
            "project_id": handle.project_id,
            "answer": assistant_answer,
        }