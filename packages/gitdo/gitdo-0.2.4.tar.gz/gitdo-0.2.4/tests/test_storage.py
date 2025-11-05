"""Tests for storage functionality."""

import json
import os

from gitdo.models import TaskStatus
from gitdo.storage import Storage


def test_storage_init(storage):
    """Test storage initialization."""
    assert not storage.is_initialized()
    storage.init()
    assert storage.is_initialized()
    assert storage.storage_dir.exists()
    assert storage.tasks_file.exists()


def test_add_task(initialized_storage):
    """Test adding a task."""
    task = initialized_storage.add_task("Test task")

    assert task.title == "Test task"
    assert task.status == TaskStatus.PENDING
    assert len(task.id) > 0


def test_load_tasks(initialized_storage):
    """Test loading tasks."""
    initialized_storage.add_task("Task 1")
    initialized_storage.add_task("Task 2")

    tasks = initialized_storage.load_tasks()
    assert len(tasks) == 2
    assert tasks[0].title == "Task 1"
    assert tasks[1].title == "Task 2"


def test_get_task(initialized_storage):
    """Test getting a task by ID."""
    task = initialized_storage.add_task("Test task")

    # Test full ID
    found_task = initialized_storage.get_task(task.id)
    assert found_task is not None
    assert found_task.id == task.id

    # Test partial ID
    found_task = initialized_storage.get_task(task.id[:8])
    assert found_task is not None
    assert found_task.id == task.id

    # Test non-existent ID
    found_task = initialized_storage.get_task("nonexistent")
    assert found_task is None


def test_complete_task(initialized_storage):
    """Test completing a task."""
    task = initialized_storage.add_task("Test task")

    result = initialized_storage.complete_task(task.id[:8])
    assert result is True

    completed_task = initialized_storage.get_task(task.id)
    assert completed_task.status == TaskStatus.COMPLETED
    assert completed_task.completed_at is not None


def test_complete_nonexistent_task(initialized_storage):
    """Test completing a non-existent task."""
    result = initialized_storage.complete_task("nonexistent")
    assert result is False


def test_remove_task(initialized_storage):
    """Test removing a task."""
    task = initialized_storage.add_task("Test task")

    result = initialized_storage.remove_task(task.id[:8])
    assert result is True

    tasks = initialized_storage.load_tasks()
    assert len(tasks) == 0


def test_remove_nonexistent_task(initialized_storage):
    """Test removing a non-existent task."""
    result = initialized_storage.remove_task("nonexistent")
    assert result is False


def test_persistence(storage):
    """Test that tasks persist across storage instances."""
    storage.init()
    task = storage.add_task("Test task")

    # Create new storage instance with same path
    new_storage = type(storage)(base_path=storage.base_path)
    tasks = new_storage.load_tasks()

    assert len(tasks) == 1
    assert tasks[0].id == task.id
    assert tasks[0].title == task.title


def test_tasks_json_format(initialized_storage):
    """Test that tasks.json has correct format."""
    task = initialized_storage.add_task("Test task")

    with open(initialized_storage.tasks_file) as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == task.id
    assert data[0]["title"] == "Test task"


def test_find_gitdo_root_in_current_dir(temp_dir):
    """Test finding .gitdo/ in current directory."""
    gitdo_dir = temp_dir / ".gitdo"
    gitdo_dir.mkdir()

    found_root = Storage._find_gitdo_root(temp_dir)
    assert found_root == temp_dir.resolve()


def test_find_gitdo_root_in_parent_dir(temp_dir):
    """Test finding .gitdo/ in parent directory."""
    gitdo_dir = temp_dir / ".gitdo"
    gitdo_dir.mkdir()

    # Create a subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    found_root = Storage._find_gitdo_root(subdir)
    assert found_root == temp_dir.resolve()


def test_find_gitdo_root_multiple_levels_up(temp_dir):
    """Test finding .gitdo/ multiple levels up the directory tree."""
    gitdo_dir = temp_dir / ".gitdo"
    gitdo_dir.mkdir()

    # Create nested subdirectories
    deep_dir = temp_dir / "level1" / "level2" / "level3"
    deep_dir.mkdir(parents=True)

    found_root = Storage._find_gitdo_root(deep_dir)
    assert found_root == temp_dir.resolve()


def test_find_gitdo_root_not_found(temp_dir):
    """Test when .gitdo/ is not found anywhere."""
    # Don't create .gitdo/ folder
    found_root = Storage._find_gitdo_root(temp_dir)
    assert found_root is None


def test_storage_uses_walk_up_logic(temp_dir):
    """Test that Storage initialization uses walk-up logic."""
    # Create .gitdo/ in parent directory
    gitdo_dir = temp_dir / ".gitdo"
    gitdo_dir.mkdir()
    (gitdo_dir / "tasks.json").write_text("[]")

    # Create a subdirectory and change to it
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        # Create storage without base_path - should find parent's .gitdo/
        storage = Storage()
        assert storage.base_path == temp_dir.resolve()
        assert storage.storage_dir == gitdo_dir.resolve()
    finally:
        os.chdir(original_cwd)


def test_storage_falls_back_to_cwd_when_not_found(temp_dir):
    """Test that Storage falls back to current directory when .gitdo/ not found."""
    # Don't create .gitdo/ folder anywhere
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        storage = Storage()
        assert storage.base_path == temp_dir.resolve()
    finally:
        os.chdir(original_cwd)


def test_storage_explicit_base_path_skips_walk_up(temp_dir):
    """Test that explicit base_path parameter skips walk-up logic."""
    # Create .gitdo/ in one directory
    gitdo_dir = temp_dir / ".gitdo"
    gitdo_dir.mkdir()

    # Create another directory without .gitdo/
    other_dir = temp_dir / "other"
    other_dir.mkdir()

    # Explicitly set base_path - should not use walk-up logic
    storage = Storage(base_path=other_dir)
    assert storage.base_path == other_dir
    assert storage.storage_dir == other_dir / ".gitdo"


def test_nested_projects_independent_storage(temp_dir):
    """Test that nested projects have independent storage."""
    # Create parent project
    parent_storage = Storage(base_path=temp_dir)
    parent_storage.init()
    parent_task = parent_storage.add_task("Parent task")

    # Create child project
    child_dir = temp_dir / "child"
    child_dir.mkdir()
    child_storage = Storage(base_path=child_dir)
    child_storage.init()
    child_task = child_storage.add_task("Child task")

    # Verify parent only has parent task
    parent_tasks = parent_storage.load_tasks()
    assert len(parent_tasks) == 1
    assert parent_tasks[0].id == parent_task.id
    assert parent_tasks[0].title == "Parent task"

    # Verify child only has child task
    child_tasks = child_storage.load_tasks()
    assert len(child_tasks) == 1
    assert child_tasks[0].id == child_task.id
    assert child_tasks[0].title == "Child task"

    # Verify storage files are separate
    assert (temp_dir / ".gitdo" / "tasks.json").exists()
    assert (child_dir / ".gitdo" / "tasks.json").exists()


def test_nested_init_allows_multiple_gitdo_folders(temp_dir):
    """Test that multiple .gitdo folders can exist in nested directories."""
    # Initialize parent
    parent_storage = Storage(base_path=temp_dir)
    parent_storage.init()
    assert parent_storage.is_initialized()

    # Initialize child with explicit base_path
    child_dir = temp_dir / "subdir"
    child_dir.mkdir()
    child_storage = Storage(base_path=child_dir)

    # Child should not be initialized yet
    assert not child_storage.is_initialized()

    # Initialize child
    child_storage.init()
    assert child_storage.is_initialized()

    # Both should be initialized independently
    assert (temp_dir / ".gitdo").exists()
    assert (child_dir / ".gitdo").exists()


def test_nested_storage_walk_up_stops_at_first_gitdo(temp_dir):
    """Test that walk-up stops at the nearest .gitdo folder."""
    # Create parent project
    parent_gitdo = temp_dir / ".gitdo"
    parent_gitdo.mkdir()
    (parent_gitdo / "tasks.json").write_text('[{"id": "parent-task", "title": "Parent"}]')

    # Create nested child project
    child_dir = temp_dir / "child"
    child_dir.mkdir()
    child_gitdo = child_dir / ".gitdo"
    child_gitdo.mkdir()
    (child_gitdo / "tasks.json").write_text('[{"id": "child-task", "title": "Child"}]')

    # Create subdirectory under child
    subdir = child_dir / "subdir"
    subdir.mkdir()

    # Storage from subdir should find child's .gitdo, not parent's
    found_root = Storage._find_gitdo_root(subdir)
    assert found_root == child_dir.resolve()

    # Change to subdir and create storage without base_path
    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        storage = Storage()
        assert storage.base_path == child_dir.resolve()
        assert storage.storage_dir == child_gitdo.resolve()
    finally:
        os.chdir(original_cwd)


def test_deeply_nested_projects(temp_dir):
    """Test multiple levels of nested projects."""
    # Create directory structure
    level1 = temp_dir / "level1"
    level2 = level1 / "level2"
    level3 = level2 / "level3"
    level1.mkdir()
    level2.mkdir()
    level3.mkdir()

    # Initialize at each level
    storage_root = Storage(base_path=temp_dir)
    storage_root.init()

    storage_l1 = Storage(base_path=level1)
    storage_l1.init()

    storage_l2 = Storage(base_path=level2)
    storage_l2.init()

    storage_l3 = Storage(base_path=level3)
    storage_l3.init()

    # Verify all are initialized independently
    assert (temp_dir / ".gitdo").exists()
    assert (level1 / ".gitdo").exists()
    assert (level2 / ".gitdo").exists()
    assert (level3 / ".gitdo").exists()

    # Verify walk-up finds the nearest .gitdo
    found_l3 = Storage._find_gitdo_root(level3)
    assert found_l3 == level3.resolve()

    found_l2 = Storage._find_gitdo_root(level2)
    assert found_l2 == level2.resolve()


def test_nested_projects_task_isolation(temp_dir):
    """Test that task operations are isolated between nested projects."""
    # Create and populate parent project
    parent_storage = Storage(base_path=temp_dir)
    parent_storage.init()
    parent_task = parent_storage.add_task("Parent task")
    parent_storage.complete_task(parent_task.id)

    # Create and populate child project
    child_dir = temp_dir / "child"
    child_dir.mkdir()
    child_storage = Storage(base_path=child_dir)
    child_storage.init()
    child_storage.add_task("Child task")

    # Verify parent has completed task
    parent_tasks = parent_storage.load_tasks()
    assert len(parent_tasks) == 1
    assert parent_tasks[0].status == TaskStatus.COMPLETED

    # Verify child has pending task
    child_tasks = child_storage.load_tasks()
    assert len(child_tasks) == 1
    assert child_tasks[0].status == TaskStatus.PENDING

    # Removing from parent shouldn't affect child
    parent_storage.remove_task(parent_task.id)
    assert len(parent_storage.load_tasks()) == 0
    assert len(child_storage.load_tasks()) == 1
