from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


SEARCH_REPOSITORY_TEXT_TOOL = OllamaToolModule(
    name="search_repository_text",
    prompt_fragment=(
        "Use the search_repository_text tool when you need to find matching text in the bound local "
        "repository. The tool supports an optional relative repository path and always applies the "
        "configured ignore paths."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "search_repository_text",
            "description": (
                "Search the bound local repository for matching text using ripgrep. Supports an optional "
                "relative repository path and always applies the configured ignore paths."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The text or regex pattern to search for in the repository.",
                    },
                    "relative_repo_path": {
                        "type": "string",
                        "description": "Optional repository-relative path to limit where the search runs.",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the repository search should be case sensitive.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of matching lines to return.",
                    },
                },
                "required": ["query"],
            },
        },
    },
)


register_tool(SEARCH_REPOSITORY_TEXT_TOOL)
