"""Error codes and exception classes for OpenSpec MCP."""

from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for OpenSpec operations."""

    NOT_INITIALIZED = "NOT_INITIALIZED"
    CHANGE_NOT_FOUND = "CHANGE_NOT_FOUND"
    CHANGE_EXISTS = "CHANGE_EXISTS"
    SPEC_NOT_FOUND = "SPEC_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FILE_SYSTEM_ERROR = "FILE_SYSTEM_ERROR"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    ARCHIVE_FAILED = "ARCHIVE_FAILED"


class OpenSpecError(Exception):
    """Base exception for OpenSpec operations."""

    def __init__(self, message: str, code: ErrorCode, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class NotInitializedError(OpenSpecError):
    """Raised when OpenSpec project is not initialized."""

    def __init__(self, path: str):
        super().__init__(
            f"OpenSpec not initialized in {path}. Run init_openspec first.",
            ErrorCode.NOT_INITIALIZED,
            {"path": path, "suggestion": "Use init_openspec tool to initialize the project"},
        )


class ChangeNotFoundError(OpenSpecError):
    """Raised when a change is not found."""

    def __init__(self, change_id: str):
        super().__init__(
            f"Change '{change_id}' not found",
            ErrorCode.CHANGE_NOT_FOUND,
            {"change_id": change_id, "suggestion": "Use list_changes to see available changes"},
        )


class ChangeExistsError(OpenSpecError):
    """Raised when trying to create a change that already exists."""

    def __init__(self, change_id: str):
        super().__init__(
            f"Change '{change_id}' already exists",
            ErrorCode.CHANGE_EXISTS,
            {
                "change_id": change_id,
                "suggestion": "Use a different change ID or show_change to view existing change",
            },
        )


class SpecNotFoundError(OpenSpecError):
    """Raised when a spec is not found."""

    def __init__(self, spec_id: str):
        super().__init__(
            f"Spec '{spec_id}' not found",
            ErrorCode.SPEC_NOT_FOUND,
            {"spec_id": spec_id, "suggestion": "Use list_specs to see available specs"},
        )


class ValidationError(OpenSpecError):
    """Raised when validation fails."""

    def __init__(self, message: str, issues: list[dict]):
        super().__init__(
            message, ErrorCode.VALIDATION_FAILED, {"issues": issues, "suggestion": "Fix validation errors and try again"}
        )


class FileSystemError(OpenSpecError):
    """Raised when file system operations fail."""

    def __init__(self, message: str, path: str):
        super().__init__(
            message, ErrorCode.FILE_SYSTEM_ERROR, {"path": path, "suggestion": "Check file permissions and disk space"}
        )
