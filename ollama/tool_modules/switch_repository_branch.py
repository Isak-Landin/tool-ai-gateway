from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


SWITCH_REPOSITORY_BRANCH_TOOL = OllamaToolModule(
    name="switch_repository_branch",
    prompt_fragment=(
        "Use the switch_repository_branch tool when the user explicitly wants work to happen on a different "
        "repository branch. This only applies to the bound local repository."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "switch_repository_branch",
            "description": (
                "Switch the bound local repository to a different branch. Optionally pull from origin after "
                "the switch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {
                        "type": "string",
                        "description": "The repository branch to switch to.",
                    },
                    "pull_from_origin": {
                        "type": "boolean",
                        "description": "Whether to pull from origin after switching branches.",
                    },
                },
                "required": ["branch_name"],
            },
        },
    },
)


register_tool(SWITCH_REPOSITORY_BRANCH_TOOL)
