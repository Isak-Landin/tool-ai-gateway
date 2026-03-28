def execute_return_to_user(completed: bool) -> dict:
    if not isinstance(completed, bool):
        raise ValueError("return_to_user completed must be a boolean")

    return {
        "completed": completed,
    }
