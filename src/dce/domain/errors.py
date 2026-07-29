"""Domain-level errors."""


class DceError(Exception):
    """Base error for DCE domain and application failures."""

    def __init__(self, message: str, *, code: str = "dce_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationError(DceError):
    """Raised when domain validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class StorageError(DceError):
    """Raised when persistence operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="storage_error")


class WorkspaceError(DceError):
    """Raised when workspace init/doctor operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="workspace_error")
