"""Data models for validation results."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IssueLevel(str, Enum):
    """Validation issue severity levels."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    level: IssueLevel
    file: str
    message: str
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """Represents validation results."""

    valid: bool
    issues: list[ValidationIssue]
