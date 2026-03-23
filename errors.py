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
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RoutePersistenceError(PersistenceError):
    """Route-facing persistence error"""


class ResolutionPersistenceError(PersistenceError):
    """Project resolution persistence error"""


class RuntimeBindingPersistenceError(PersistenceError):
    """Runtime binding persistence error"""


class ProjectHandlePersistenceError(PersistenceError):
    """Project handle persistence error"""


class ExecutionPersistenceError(PersistenceError):
    """Execution persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class MessageHistoryPersistenceError(PersistenceError):
    """Message history persistence error"""


class RepositoryFilePersistenceError(PersistenceError):
    """Repository file persistence error"""
