class PersistenceError(Exception):
    """Database operation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field  # Which field caused the error (e.g., "ssh_key")
        super().__init__(message)

class FileProcessingError(Exception):
    """File processing error"""
    pass

class GitHubError(Exception):
    """Git operation error"""
    pass