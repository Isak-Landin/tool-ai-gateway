from project_handle import ProjectHandle
from ollama.ollama_client import call_ollama
from archon.archon import archon_search, archon_rag_query


class WorkflowExecutionError(Exception):
    pass


class WorkflowOrchestrator:
    def _build_history(self, history_rows: list[dict]) -> list[dict]:
        history: list[dict] = []

        for row in history_rows:
            message: dict = {
                "role": row.get("role"),
                "content": row.get("content") or "",
            }

            thinking = row.get("thinking")
            if thinking:
                message["thinking"] = thinking

            tool_calls = row.get("tool_calls_json")
            if tool_calls:
                message["tool_calls"] = tool_calls

            history.append(message)

        return history

    def _collect_selected_context(self, handle: ProjectHandle, selected_files: list[str]) -> list[str]:
        if not selected_files:
            return []

        file_rows = handle.files.list_by_project()
        selected_names = set(selected_files)

        selected_context: list[str] = []
        for file_row in file_rows:
            if file_row.get("name") in selected_names and file_row.get("content"):
                selected_context.append(file_row["content"])

        return selected_context

    def _execute_tool_call(self, tool_call: dict) -> tuple[str, dict]:
        function_data = tool_call.get("function") or {}
        tool_name = function_data.get("name") or ""
        arguments = function_data.get("arguments") or {}

        if not tool_name:
            raise WorkflowExecutionError("Ollama returned a tool call without function.name")

        if not isinstance(arguments, dict):
            raise WorkflowExecutionError("Ollama returned non-dict tool arguments")

        if tool_name == "archon_search":
            return tool_name, archon_search(**arguments)

        if tool_name == "archon_rag_query":
            return tool_name, archon_rag_query(**arguments)

        raise WorkflowExecutionError(f"Unknown tool: {tool_name}")

    def run_chat(self, handle: ProjectHandle, message: str, selected_files: list[str] | None = None) -> dict:
        if handle is None:
            raise WorkflowExecutionError("ProjectHandle is required")

        if not str(message).strip():
            raise WorkflowExecutionError("message is required")

        if selected_files is None:
            selected_files = []

        history_rows = handle.messages.list_by_project()
        history = self._build_history(history_rows)

        selected_context = self._collect_selected_context(handle, selected_files)

        effective_message = message
        if selected_context:
            effective_message = message + "\n\n" + "\n\n".join(selected_context)

        sequence_no = len(history_rows) + 1

        # Persist user turn first
        handle.messages.insert_message(
            {
                "project_id": handle.project_id,
                "sequence_no": sequence_no,
                "role": "user",
                "content": effective_message,
                "raw_message_json": {
                    "role": "user",
                    "content": effective_message,
                },
            }
        )
        sequence_no += 1

        response = call_ollama(effective_message, history)

        ollama_message = response.get("message") or {}
        assistant_content = ollama_message.get("content") or ""
        assistant_thinking = ollama_message.get("thinking")
        assistant_tool_calls = ollama_message.get("tool_calls") or []

        if assistant_tool_calls:
            # Persist the native assistant tool-call turn exactly as returned
            handle.messages.insert_message(
                {
                    "project_id": handle.project_id,
                    "sequence_no": sequence_no,
                    "role": "assistant",
                    "content": assistant_content or None,
                    "thinking": assistant_thinking,
                    "tool_calls_json": assistant_tool_calls,
                    "raw_message_json": ollama_message,
                    "raw_response_json": response,
                }
            )
            sequence_no += 1

            # Execute each requested tool and persist its result
            for tool_call in assistant_tool_calls:
                tool_name, tool_result = self._execute_tool_call(tool_call)

                handle.messages.insert_message(
                    {
                        "project_id": handle.project_id,
                        "sequence_no": sequence_no,
                        "role": "tool",
                        "content": str(tool_result),
                        "tool_name": tool_name,
                        "raw_message_json": {
                            "role": "tool",
                            "content": str(tool_result),
                        },
                        "raw_response_json": tool_result,
                    }
                )
                sequence_no += 1

            raise WorkflowExecutionError(
                "Native Ollama tool follow-up requires ollama/ollama_client.py and ollama/builder.py "
                "to support full message-history requests with tools."
            )

        # Final non-tool assistant turn
        handle.messages.insert_message(
            {
                "project_id": handle.project_id,
                "sequence_no": sequence_no,
                "role": "assistant",
                "content": assistant_content,
                "thinking": assistant_thinking,
                "raw_message_json": ollama_message,
                "raw_response_json": response,
            }
        )

        return {
            "ok": True,
            "execution_type": "chat",
            "project_id": handle.project_id,
            "answer": assistant_content,
        }