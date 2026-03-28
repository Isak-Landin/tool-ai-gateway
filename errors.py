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


class ProjectBootstrapError(Exception):
    """Project bootstrap runtime error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        self.message = message
        self.field = field
        self.error_type = error_type
        self.file_id = file_id
        super().__init__(message)


# PERSISTENCE LAYER ERROR REPRESENTATION
class ProjectPersistenceError(PersistenceError):
    """Project entity persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class ResolutionPersistenceError(PersistenceError):
    """Project resolution persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class RuntimeBindingPersistenceError(PersistenceError):
    """Runtime binding persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class BoundProjectRuntimePersistenceError(PersistenceError):
    """Bound project runtime persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class ExecutionPersistenceError(PersistenceError):
    """Execution persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class MessageHistoryPersistenceError(PersistenceError):
    """Message history persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id


class RepositoryFilePersistenceError(PersistenceError):
    """Repository file persistence error"""
    def __init__(self, message: str, field: str = None, error_type: str = None, file_id: str = None):
        super().__init__(message=message, field=field, error_type=error_type)
        self.file_id = file_id
