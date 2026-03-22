import os


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")


def get_ollama_default_model() -> str:
    return os.getenv("OLLAMA_MODEL", "seamon67/Ministral-3-Reasoning:14b")


def get_default_chat_options() -> dict:
    return {
        "stream": False,
    }
