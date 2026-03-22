# errors.py
class PersistenceError(Exception):
    """Database operation error"""
    def __init__(self, message: str, field: str = None, error_type: str = None):
        self.message = message
        self.field = field
        self.error_type = error_type
        super().__init__(message)


class FileProcessingError(Exception):
    """File processing error"""
    pass


class GitHubError(Exception):
    """Git operation error"""
    pass