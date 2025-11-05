"""Markdown file parser for extracting tasks."""

import re
from pathlib import Path
from uuid import uuid4

from .models import Task, TaskStatus


def extract_checkbox_items(content: str) -> list[tuple[str, bool]]:
    """Extract checkbox items from markdown content.

    Args:
        content: Markdown file content

    Returns:
        List of (title, is_completed) tuples
    """
    # Pattern matches: - [ ] or - [x] or - [X] followed by task title
    # Supports various indentation levels
    pattern = r"^\s*-\s+\[([ xX])\]\s+(.+)$"
    items = []

    for line in content.splitlines():
        match = re.match(pattern, line)
        if match:
            checkbox_state = match.group(1)
            title = match.group(2).strip()
            is_completed = checkbox_state.lower() == "x"
            items.append((title, is_completed))

    return items


def parse_markdown_file(file_path: Path) -> list[Task]:
    """Parse markdown file and extract tasks.

    Args:
        file_path: Path to markdown file

    Returns:
        List of Task objects extracted from checkbox items

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        content = file_path.read_text()
    except PermissionError as e:
        raise PermissionError(f"Cannot read file: {file_path}") from e

    checkbox_items = extract_checkbox_items(content)
    tasks = []

    for title, is_completed in checkbox_items:
        task = Task(
            id=str(uuid4()),
            title=title,
            status=TaskStatus.COMPLETED if is_completed else TaskStatus.PENDING,
        )
        if is_completed:
            task.complete()

        tasks.append(task)

    return tasks
