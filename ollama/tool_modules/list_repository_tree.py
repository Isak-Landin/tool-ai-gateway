from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


LIST_REPOSITORY_TREE_TOOL = OllamaToolModule(
    name="list_repository_tree",
    prompt_fragment=(
        "Use the list_repository_tree tool when you need a tree-style repository listing from the bound "
        "project repository. The tool is served by the bound FileRuntime surface, supports an optional "
        "relative repository path, and applies the configured ignore paths against the active branch."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "list_repository_tree",
            "description": (
                "List the bound project repository tree from the repository root or an optional relative "
                "path using the active branch and configured ignore paths."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_repo_path": {
                        "type": "string",
                        "description": "Optional repository-relative path to list instead of the full root.",
                    }
                },
                "required": [],
            },
        },
    },
)


register_tool(LIST_REPOSITORY_TREE_TOOL)
