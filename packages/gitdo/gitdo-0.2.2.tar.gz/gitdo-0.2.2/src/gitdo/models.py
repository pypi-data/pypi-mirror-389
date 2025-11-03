"""Data models for GitDo."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class Task:
    """Task model."""

    id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
        )
