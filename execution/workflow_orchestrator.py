"""
Execution layer rules and intended behavior.

Layer rule summary:

- This layer is called only after request entry has already validated transport
  input and, for project-scoped runtime work, after project resolution and
  runtime binding have already succeeded.
- This layer receives project-scoped execution input plus a usable bound runtime.
- This layer returns execution result data upward, but does not shape HTTP
  status codes, route payloads, or transport-specific errors.

Being called from above:

- request entry invokes execution only for routes that truly need project-scoped
  behavior
- project resolution owns finding the project row
- runtime binding owns constructing the usable runtime/handle
- execution should assume it receives an already-bound runtime surface rather
  than performing route parsing or runtime construction itself

Calling downward:

- execution calls persistence-owned surfaces to load prior state and persist
  execution-owned results
- execution calls model invocation surfaces when a prompt or message set is
  ready to be executed
- execution calls tool, git, or other runtime surfaces only as part of
  orchestrated project behavior

Execution ownership:

- workflow ordering
- context assembly
- model/tool sequencing
- execution-owned persistence ordering
- translation between a bound runtime and lower-level module calls

Execution does not own:

- HTTP parsing or response shaping
- project lookup
- runtime construction
- database bootstrap
- route-level error mapping

Intended chat run:

1. accept a bound project runtime and validated chat input
2. validate execution-specific preconditions
3. load a bounded recent project history window
4. load selected project context from the current local repository state
5. decide tool availability and choose run context deterministically
6. build the model-ready message/input set
7. persist the user turn
8. execute the model call
9. if tool calls are returned:
   - persist the assistant tool-call turn
   - execute tool calls in order
   - persist tool results
   - continue the run until a final assistant answer is produced
10. persist the final assistant turn
11. return execution result data upward
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from functools import partial
from typing import Any, Callable

from ollama.builder import (
    append_assistant_message,
    append_chat_message,
    append_system_message,
    append_tool_message,
    append_user_message,
    build_chat_message,
    create_chat_envelope,
    merge_chat_envelope_fields,
)
from ollama.config import get_ollama_default_model
from ollama.ollama_client import parse_model_output, send_chat_envelope
from ollama.prompts import merge_system_prompt_fragments
from ollama.tool_registry import build_tool_prompt_fragment, build_tool_schemas
from BoundProjectRuntime import BoundProjectRuntime
from tools import (
    execute_list_repository_tree,
    execute_return_to_user,
    execute_search_repository_text,
    execute_web_search,
)


DEFAULT_RECENT_HISTORY_LIMIT = int(os.getenv("EXECUTION_RECENT_HISTORY_LIMIT", "20"))


class WorkflowExecutionError(Exception):
    pass


class WorkflowOrchestrator:
    def _get_execution_model(self, handle: BoundProjectRuntime) -> str:
        model_name = getattr(handle, "ai_model_name", None)
        if str(model_name).strip():
            return str(model_name).strip()

        return get_ollama_default_model()

    def _require_execution_persistence(self, handle: BoundProjectRuntime):
        execution_persistence = getattr(handle, "execution_persistence", None)
        if execution_persistence is None:
            raise WorkflowExecutionError("BoundProjectRuntime.execution_persistence is required")

        return execution_persistence

    def _get_recent_history_limit(self) -> int:
        if DEFAULT_RECENT_HISTORY_LIMIT < 1:
            raise WorkflowExecutionError("EXECUTION_RECENT_HISTORY_LIMIT must be >= 1")

        return DEFAULT_RECENT_HISTORY_LIMIT

    def _build_ollama_history_messages(self, history_rows: list[dict]) -> list[dict]:
        history_messages: list[dict] = []

        for row in history_rows:
            history_messages.append(
                build_chat_message(
                    role=row.get("role"),
                    content=row.get("content"),
                    tool_calls=row.get("tool_calls_json"),
                    tool_name=row.get("tool_name"),
                    images=row.get("images_json"),
                    thinking=row.get("thinking"),
                )
            )

        return history_messages

    def _build_selected_context_block(self, selected_context_rows: list[dict]) -> str | None:
        selected_context_sections: list[str] = []

        for selected_context_row in selected_context_rows:
            file_identity = selected_context_row.get("path") or selected_context_row.get("name") or "unknown"
            file_content = selected_context_row.get("content")
            if not file_content:
                continue

            selected_context_sections.append(f"File: {file_identity}\n{file_content}")

        if not selected_context_sections:
            return None

        return "Selected file context for this run:\n\n" + "\n\n".join(selected_context_sections)

    def _build_user_turn_content(self, user_message: str, selected_context_rows: list[dict]) -> str:
        selected_context_block = self._build_selected_context_block(selected_context_rows)
        if selected_context_block is None:
            return user_message

        return user_message + "\n\n" + selected_context_block

    def _require_repo_path(self, handle: BoundProjectRuntime) -> str:
        repo_path = getattr(handle, "repo_path", None)
        if not str(repo_path).strip():
            raise WorkflowExecutionError("BoundProjectRuntime.repo_path is required for repository tools")

        return repo_path

    def _require_repository_runtime(self, handle: BoundProjectRuntime):
        repository_runtime = getattr(handle, "repository_runtime", None)
        if repository_runtime is None:
            raise WorkflowExecutionError("BoundProjectRuntime.repository_runtime is required for shell-backed tools")

        return repository_runtime

    def _run_repository_text_search(
        self,
        handle: BoundProjectRuntime,
        query: str,
        relative_repo_path: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> list[dict]:
        repository_runtime = self._require_repository_runtime(handle)
        return execute_search_repository_text(
            shell_executor=repository_runtime.shell,
            repo_path=repository_runtime.repo_path,
            query=query,
            relative_repo_path=relative_repo_path,
            case_sensitive=case_sensitive,
            max_results=max_results,
        )

    def _run_repository_tree_listing(
        self,
        handle: BoundProjectRuntime,
        relative_repo_path: str | None = None,
    ) -> list[dict]:
        repository_runtime = self._require_repository_runtime(handle)
        return execute_list_repository_tree(
            shell_executor=repository_runtime.shell,
            repo_path=repository_runtime.repo_path,
            relative_repo_path=relative_repo_path,
        )

    def _get_tool_executors(self, handle: BoundProjectRuntime) -> dict[str, Callable[..., Any]]:
        return {
            "return_to_user": execute_return_to_user,
            "web_search": execute_web_search,
            "search_repository_text": partial(self._run_repository_text_search, handle),
            "list_repository_tree": partial(self._run_repository_tree_listing, handle),
        }

    def _select_chat_tool_names(self, handle: BoundProjectRuntime) -> list[str]:
        return list(self._get_tool_executors(handle).keys())

    def _parse_ollama_created_at(self, created_at_value: str | None) -> datetime | None:
        if created_at_value is None:
            return None

        normalized_value = created_at_value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized_value)
        except ValueError as e:
            raise WorkflowExecutionError(f"Invalid Ollama created_at value: {created_at_value}") from e

    def _build_assistant_artifact_data(self, sequence_no: int, parsed_output: dict) -> dict:
        return {
            "sequence_no": sequence_no,
            "role": "assistant",
            "content": parsed_output.get("content"),
            "thinking": parsed_output.get("thinking"),
            "tool_calls_json": parsed_output.get("tool_calls") or None,
            "tool_name": parsed_output.get("tool_name"),
            "images_json": parsed_output.get("images"),
            "ollama_model": parsed_output.get("model"),
            "ollama_created_at": self._parse_ollama_created_at(parsed_output.get("created_at")),
            "done": parsed_output.get("done"),
            "done_reason": parsed_output.get("done_reason"),
            "total_duration": parsed_output.get("total_duration"),
            "load_duration": parsed_output.get("load_duration"),
            "prompt_eval_count": parsed_output.get("prompt_eval_count"),
            "prompt_eval_duration": parsed_output.get("prompt_eval_duration"),
            "eval_count": parsed_output.get("eval_count"),
            "eval_duration": parsed_output.get("eval_duration"),
            "raw_message_json": parsed_output.get("message"),
            "raw_response_json": parsed_output.get("raw_response"),
        }

    def _serialize_tool_result_content(self, tool_result: Any) -> str:
        if isinstance(tool_result, str):
            return tool_result

        try:
            return json.dumps(tool_result, ensure_ascii=True)
        except TypeError as e:
            raise WorkflowExecutionError("Tool result is not JSON serializable") from e

    def _execute_tool_call(self, handle: BoundProjectRuntime, tool_call: dict) -> tuple[str, Any]:
        function_data = tool_call.get("function") or {}
        tool_name = function_data.get("name") or ""
        arguments = function_data.get("arguments") or {}

        if not tool_name:
            raise WorkflowExecutionError("Ollama returned a tool call without function.name")

        if not isinstance(arguments, dict):
            raise WorkflowExecutionError("Ollama returned non-dict tool arguments")

        tool_executor = self._get_tool_executors(handle).get(tool_name)
        if tool_executor is None:
            raise WorkflowExecutionError(f"Unknown tool: {tool_name}")

        try:
            return tool_name, tool_executor(**arguments)
        except TypeError as e:
            raise WorkflowExecutionError(f"Invalid arguments for tool '{tool_name}'") from e
        except ValueError as e:
            raise WorkflowExecutionError(f"Invalid arguments for tool '{tool_name}'") from e

    def _extract_return_to_user_call(self, assistant_tool_calls: list[dict]) -> dict | None:
        return_calls = [
            tool_call
            for tool_call in assistant_tool_calls
            if ((tool_call.get("function") or {}).get("name") == "return_to_user")
        ]
        if not return_calls:
            return None

        if len(return_calls) != 1 or len(assistant_tool_calls) != 1:
            raise WorkflowExecutionError(
                "return_to_user must be the only tool call in its assistant turn"
            )

        return return_calls[0]

    def _build_chat_envelope(
        self,
        handle: BoundProjectRuntime,
        history_messages: list[dict],
        user_turn_content: str,
        tool_names: list[str],
    ) -> dict:
        chat_envelope = create_chat_envelope(model=self._get_execution_model(handle))

        tool_prompt_fragment = build_tool_prompt_fragment(tool_names)
        effective_system_prompt = merge_system_prompt_fragments(
            base_system_prompt=None,
            extra_fragments=[tool_prompt_fragment] if tool_prompt_fragment else None,
        )
        append_system_message(chat_envelope, system_prompt=effective_system_prompt)

        for history_message in history_messages:
            append_chat_message(chat_envelope, history_message)

        append_user_message(chat_envelope, user_turn_content)

        if tool_names:
            merge_chat_envelope_fields(
                chat_envelope,
                tools=build_tool_schemas(tool_names),
            )

        return chat_envelope

    def run_chat(self, handle: BoundProjectRuntime, message: str, selected_files: list[str] | None = None) -> dict:
        if handle is None:
            raise WorkflowExecutionError("BoundProjectRuntime is required")

        if not str(message).strip():
            raise WorkflowExecutionError("message is required")

        execution_persistence = self._require_execution_persistence(handle)
        selected_file_names = selected_files or []

        history_rows = execution_persistence.load_recent_history(limit=self._get_recent_history_limit())
        history_messages = self._build_ollama_history_messages(history_rows)

        selected_context_rows = execution_persistence.load_selected_context(selected_file_names)
        user_turn_content = self._build_user_turn_content(message, selected_context_rows)

        tool_names = self._select_chat_tool_names(handle)
        chat_envelope = self._build_chat_envelope(
            handle=handle,
            history_messages=history_messages,
            user_turn_content=user_turn_content,
            tool_names=tool_names,
        )

        sequence_no = execution_persistence.load_next_sequence_no()
        execution_persistence.store_artifact(
            {
                "sequence_no": sequence_no,
                "role": "user",
                "content": user_turn_content,
                "raw_message_json": build_chat_message(role="user", content=user_turn_content),
            }
        )
        sequence_no += 1

        while True:
            parsed_output = parse_model_output(send_chat_envelope(chat_envelope))
            assistant_content = parsed_output.get("content")
            assistant_thinking = parsed_output.get("thinking")
            assistant_tool_calls = parsed_output.get("tool_calls") or []
            assistant_images = parsed_output.get("images")

            execution_persistence.store_artifact(
                self._build_assistant_artifact_data(sequence_no=sequence_no, parsed_output=parsed_output)
            )
            sequence_no += 1

            return_to_user_tool_call = self._extract_return_to_user_call(assistant_tool_calls)
            if return_to_user_tool_call is not None:
                tool_name, tool_result = self._execute_tool_call(handle, return_to_user_tool_call)
                tool_result_content = self._serialize_tool_result_content(tool_result)

                execution_persistence.store_artifact(
                    {
                        "sequence_no": sequence_no,
                        "role": "tool",
                        "content": tool_result_content,
                        "tool_name": tool_name,
                        "raw_message_json": build_chat_message(
                            role="tool",
                            content=tool_result_content,
                            tool_name=tool_name,
                        ),
                        "raw_response_json": {
                            "tool_call": return_to_user_tool_call,
                            "tool_result": tool_result,
                        },
                    }
                )

                return {
                    "ok": True,
                    "execution_type": "chat",
                    "project_id": handle.project_id,
                    "answer": assistant_content or "",
                    "return_to_user": tool_result,
                }

            append_assistant_message(
                chat_envelope,
                content=assistant_content,
                tool_calls=assistant_tool_calls,
                images=assistant_images,
                thinking=assistant_thinking,
            )

            for tool_call in assistant_tool_calls:
                tool_name, tool_result = self._execute_tool_call(handle, tool_call)
                tool_result_content = self._serialize_tool_result_content(tool_result)

                execution_persistence.store_artifact(
                    {
                        "sequence_no": sequence_no,
                        "role": "tool",
                        "content": tool_result_content,
                        "tool_name": tool_name,
                        "raw_message_json": build_chat_message(
                            role="tool",
                            content=tool_result_content,
                            tool_name=tool_name,
                        ),
                        "raw_response_json": {
                            "tool_call": tool_call,
                            "tool_result": tool_result,
                        },
                    }
                )
                sequence_no += 1

                append_tool_message(
                    chat_envelope,
                    content=tool_result_content,
                    tool_name=tool_name,
                )
