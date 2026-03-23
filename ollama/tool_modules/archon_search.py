from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


ARCHON_SEARCH_TOOL = OllamaToolModule(
    name="archon_search",
    prompt_fragment=(
        "Use the archon_search tool when you need project knowledge retrieval chunks "
        "instead of a synthesized final answer."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "archon_search",
            "description": "Search Archon knowledge items and return matching project knowledge chunks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to run against Archon knowledge.",
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional source filter for the Archon search.",
                    },
                    "match_count": {
                        "type": "integer",
                        "description": "Maximum number of matches to return.",
                    },
                    "return_mode": {
                        "type": "string",
                        "description": "How Archon should shape the returned search data.",
                    },
                },
                "required": ["query"],
            },
        },
    },
)


register_tool(ARCHON_SEARCH_TOOL)
