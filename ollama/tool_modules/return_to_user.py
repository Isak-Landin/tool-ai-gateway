from ollama.tool_module import OllamaToolModule
from ollama.tool_registry import register_tool


RETURN_TO_USER_TOOL = OllamaToolModule(
    name="return_to_user",
    prompt_fragment=(
        "Use the return_to_user tool only when execution should hand control back to the user. "
        "Set completed to true when you believe the requested work is complete for this run. "
        "Set completed to false when you need to return control to the user without claiming completion."
    ),
    schema={
        "type": "function",
        "function": {
            "name": "return_to_user",
            "description": (
                "Signal that execution should return control to the user for this run."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean",
                        "description": (
                            "Whether the requested work is complete for this run when control returns to the user."
                        ),
                    },
                },
                "required": ["completed"],
            },
        },
    },
)


register_tool(RETURN_TO_USER_TOOL)
