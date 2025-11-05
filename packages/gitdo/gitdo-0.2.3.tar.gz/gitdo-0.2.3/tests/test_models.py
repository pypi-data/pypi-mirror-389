"""Tests for task models."""

from datetime import datetime

from gitdo.models import Task, TaskStatus


def test_task_creation():
    """Test task creation."""
    task = Task(id="test-id", title="Test task")
    assert task.id == "test-id"
    assert task.title == "Test task"
    assert task.status == TaskStatus.PENDING
    assert task.completed_at is None


def test_task_complete():
    """Test marking task as completed."""
    task = Task(id="test-id", title="Test task")
    task.complete()

    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)


def test_task_to_dict():
    """Test converting task to dictionary."""
    task = Task(id="test-id", title="Test task")
    task_dict = task.to_dict()

    assert task_dict["id"] == "test-id"
    assert task_dict["title"] == "Test task"
    assert task_dict["status"] == "pending"
    assert "created_at" in task_dict
    assert task_dict["completed_at"] is None


def test_task_from_dict():
    """Test creating task from dictionary."""
    task_dict = {
        "id": "test-id",
        "title": "Test task",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    task = Task.from_dict(task_dict)

    assert task.id == "test-id"
    assert task.title == "Test task"
    assert task.status == TaskStatus.PENDING
    assert task.completed_at is None


def test_task_roundtrip():
    """Test converting task to dict and back."""
    original_task = Task(id="test-id", title="Test task")
    task_dict = original_task.to_dict()
    restored_task = Task.from_dict(task_dict)

    assert restored_task.id == original_task.id
    assert restored_task.title == original_task.title
    assert restored_task.status == original_task.status
