"""Data models for OpenSpec changes."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """Represents a task in a change."""

    id: str
    description: str
    completed: bool
    subtasks: list["Task"] = field(default_factory=list)


@dataclass
class TaskProgress:
    """Represents task completion progress."""

    completed: int
    total: int

    @property
    def percentage(self) -> int:
        """Calculate completion percentage."""
        return int((self.completed / self.total) * 100) if self.total > 0 else 0


@dataclass
class Change:
    """Represents an OpenSpec change."""

    id: str
    path: str
    proposal: str
    tasks: list[Task]
    design: Optional[str] = None
    spec_deltas: dict[str, str] = field(default_factory=dict)  # capability -> delta content
