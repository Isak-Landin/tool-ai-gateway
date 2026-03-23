from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


ARCHON_RAG_QUERY_TOOL = OllamaToolModule(
    name="archon_rag_query",
    prompt_fragment=(
        "Use the archon_rag_query tool when you need Archon to return a synthesized "
        "knowledge-grounded answer instead of raw search matches."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "archon_rag_query",
            "description": "Query Archon RAG and return a synthesized project knowledge answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask Archon RAG.",
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional source filter for the Archon RAG query.",
                    },
                    "match_count": {
                        "type": "integer",
                        "description": "Maximum number of matches to use in the RAG query.",
                    },
                    "return_mode": {
                        "type": "string",
                        "description": "How Archon should shape the returned RAG data.",
                    },
                },
                "required": ["query"],
            },
        },
    },
)


register_tool(ARCHON_RAG_QUERY_TOOL)
