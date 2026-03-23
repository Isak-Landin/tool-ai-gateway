from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


WEB_SEARCH_TOOL_MODULE = OllamaToolModule(
    name="web_search",
    prompt_fragment=(
        "When using the web_search tool, prefer it only for public, external, or time-sensitive "
        "information that is not already available in project context or local knowledge."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the public web. Use this only when external and up-to-date public "
                "information is needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query.",
                    },
                },
                "required": ["query"],
            },
        },
    },
)


register_tool(WEB_SEARCH_TOOL_MODULE)
