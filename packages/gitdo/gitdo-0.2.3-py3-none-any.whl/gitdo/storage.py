"""Storage handling for GitDo."""

import json
from pathlib import Path
from uuid import uuid4

from .models import Task


class Storage:
    """Handle task storage in .gitdo/ folder."""

    def __init__(self, base_path: Path | None = None):
        """Initialize storage.

        Args:
            base_path: Base path for storage. If None, searches for .gitdo/
                      by walking up from current directory.
        """
        if base_path is None:
            self.base_path = self._find_gitdo_root() or Path.cwd()
        else:
            self.base_path = base_path
        self.storage_dir = self.base_path / ".gitdo"
        self.tasks_file = self.storage_dir / "tasks.json"

    @staticmethod
    def _find_gitdo_root(start_path: Path | None = None) -> Path | None:
        """
        Find .gitdo/ folder by walking up directory tree.

        Args:
            start_path: Starting directory. Defaults to current directory.

        Returns:
            Path containing .gitdo/ folder, or None if not found.

        """
        current = start_path or Path.cwd()
        current = current.resolve()

        # Walk up the directory tree until we find .gitdo or reach root
        while True:
            gitdo_path = current / ".gitdo"
            if gitdo_path.exists() and gitdo_path.is_dir():
                return current

            parent = current.parent
            # Check if we've reached the filesystem root
            if parent == current:
                return None
            current = parent

    def init(self) -> None:
        """Initialize .gitdo folder and files."""
        self.storage_dir.mkdir(exist_ok=True)
        if not self.tasks_file.exists():
            self._save_tasks([])

    def is_initialized(self) -> bool:
        """Check if .gitracker folder exists."""
        return self.storage_dir.exists() and self.tasks_file.exists()

    def add_task(self, title: str) -> Task:
        """Add a new task.

        Args:
            title: Task title

        Returns:
            Created task
        """
        tasks = self.load_tasks()
        task = Task(id=str(uuid4()), title=title)
        tasks.append(task)
        self._save_tasks(tasks)
        return task

    def load_tasks(self) -> list[Task]:
        """Load all tasks from storage.

        Returns:
            List of tasks
        """
        if not self.tasks_file.exists():
            return []

        with open(self.tasks_file) as f:
            data = json.load(f)
            return [Task.from_dict(task_data) for task_data in data]

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        tasks = self.load_tasks()
        for task in tasks:
            if task.id.startswith(task_id):
                return task
        return None

    def start_task(self, task_id: str) -> bool:
        """Mark task as in progress.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and started, False otherwise
        """
        tasks = self.load_tasks()
        for task in tasks:
            if task.id.startswith(task_id):
                task.start()
                self._save_tasks(tasks)
                return True
        return False

    def complete_task(self, task_id: str) -> bool:
        """Mark task as completed.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and completed, False otherwise
        """
        tasks = self.load_tasks()
        for task in tasks:
            if task.id.startswith(task_id):
                task.complete()
                self._save_tasks(tasks)
                return True
        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove task.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and removed, False otherwise
        """
        tasks = self.load_tasks()
        for i, task in enumerate(tasks):
            if task.id.startswith(task_id):
                tasks.pop(i)
                self._save_tasks(tasks)
                return True
        return False

    def import_tasks(
        self,
        tasks: list[Task],
        *,
        skip_duplicates: bool = False,
    ) -> tuple[int, int]:
        """Import multiple tasks at once.

        Args:
            tasks: List of tasks to import
            skip_duplicates: If True, skip tasks with duplicate titles

        Returns:
            Tuple of (imported_count, skipped_count)
        """
        existing_tasks = self.load_tasks()
        existing_titles = {task.title for task in existing_tasks} if skip_duplicates else set()

        imported_count = 0
        skipped_count = 0

        for task in tasks:
            if skip_duplicates and task.title in existing_titles:
                skipped_count += 1
                continue

            existing_tasks.append(task)
            existing_titles.add(task.title)
            imported_count += 1

        self._save_tasks(existing_tasks)
        return imported_count, skipped_count

    def _save_tasks(self, tasks: list[Task]) -> None:
        """Save tasks to storage.

        Args:
            tasks: List of tasks to save
        """
        with open(self.tasks_file, "w") as f:
            json.dump([task.to_dict() for task in tasks], f, indent=2)
