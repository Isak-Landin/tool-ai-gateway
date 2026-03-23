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
- execution calls repo/file access surfaces when selected project context is
  needed
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
4. load selected project context
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

from project_handle import ProjectHandle
from ollama.ollama_client import call_ollama
from archon.archon import archon_search, archon_rag_query


class WorkflowExecutionError(Exception):
    pass


class WorkflowOrchestratorReplica:
    """
    Non-functional representation of the intended execution-layer contract.

    This class exists to show execution behavior in implementation order without
    introducing real runtime behavior yet.
    """

    def prepare_chat_run(self, bound_runtime, chat_input):
        """
        Chat entry preparation:
        - accept a bound project runtime from the runtime-binding layer
        - accept chat input that has already passed route/request checks
        - validate execution-layer preconditions for a project-scoped chat run

        This seam should not parse HTTP input or construct runtime objects.
        """
        pass

    def collect_chat_context(self, bound_runtime, chat_input):
        """
        Chat context collection:
        - load prior chat state and message history
        - load selected project context
        - decide which tool surfaces belong in the current run
        - prepare the execution-owned inputs needed before model work begins

        This seam represents chat-context assembly, not transport behavior.
        """
        pass

    def run_chat_cycle(self, chat_state):
        """
        Chat orchestration:
        - build the model-ready input set
        - execute the model call
        - execute tool/runtime calls when the workflow requires them
        - continue the model/tool cycle until a final assistant answer exists

        This seam is where execution-layer ordering belongs.
        """
        pass

    def persist_chat_run(self, chat_state, chat_outputs):
        """
        Chat persistence:
        - persist the user turn before the model call
        - persist assistant and tool artifacts in the order the workflow requires
        - keeps persistence focused on storage while execution owns sequencing

        This seam should not perform route-level response shaping.
        """
        pass

    def build_chat_result(self, chat_outputs):
        """
        Chat result shaping:
        - returns execution result data to the caller above this layer
        - leaves HTTP status codes, response models, and transport mapping to the
          request-entry layer
        """
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

        """
        Layer/rule mismatch:
        - This currently pulls selected context from persisted file rows only.
        - Under the newer execution lifecycle, this step belongs to execution, but
          the intended source is project-scoped context gathering for the current
          run, not only previously stored file snapshots.
        - The responsibility still belongs to the execution layer, but this
          implementation reflects an older, narrower context model.
        """
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

        """
        Lifecycle mismatch:
        - The newer execution lifecycle expects execution to decide tool
          availability, build a model-ready input set, and then run the cycle.
        - This direct single-call shape skips an explicit prepare-run step and
          keeps the model invocation coupled to an older one-shot flow.
        - This still belongs to the execution layer, but it does not match the
          newer staged runtime process.
        """
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

            """
            Lifecycle mismatch:
            - The intended execution lifecycle says tool work should continue
              until a final assistant answer is produced and then return result
              data upward.
            - This branch stops after persisting assistant/tool artifacts and
              raises instead of continuing the execution cycle to completion.
            - The logic belongs to execution, but the incomplete follow-up path
              no longer fits the defined runtime lifecycle.
            """
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
