"""Tests for markdown parser."""

from pathlib import Path

import pytest

from gitdo.markdown_parser import extract_checkbox_items, parse_markdown_file
from gitdo.models import TaskStatus


def test_extract_checkbox_items_basic():
    """Test extracting basic checkbox items."""
    content = """
# My Tasks

- [ ] Task 1
- [x] Task 2
- [ ] Task 3
"""
    items = extract_checkbox_items(content)
    assert len(items) == 3
    assert items[0] == ("Task 1", False)
    assert items[1] == ("Task 2", True)
    assert items[2] == ("Task 3", False)


def test_extract_checkbox_items_uppercase_x():
    """Test extracting checkbox items with uppercase X."""
    content = """
- [ ] Pending task
- [X] Completed task
- [x] Another completed task
"""
    items = extract_checkbox_items(content)
    assert len(items) == 3
    assert items[0] == ("Pending task", False)
    assert items[1] == ("Completed task", True)
    assert items[2] == ("Another completed task", True)


def test_extract_checkbox_items_with_indentation():
    """Test extracting checkbox items with various indentation levels."""
    content = """
- [ ] Level 0
  - [ ] Level 1
    - [ ] Level 2
      - [ ] Level 3
"""
    items = extract_checkbox_items(content)
    assert len(items) == 4
    assert items[0][0] == "Level 0"
    assert items[1][0] == "Level 1"
    assert items[2][0] == "Level 2"
    assert items[3][0] == "Level 3"


def test_extract_checkbox_items_mixed_content():
    """Test extracting checkbox items from mixed markdown content."""
    content = """
# Project Tasks

Some intro text here.

## Features
- [ ] Add authentication
- [x] Setup database

Not a task item
- Regular bullet point without checkbox

## Bugs
- [ ] Fix login issue
- [ ] Update dependencies

Random text
"""
    items = extract_checkbox_items(content)
    assert len(items) == 4
    assert items[0] == ("Add authentication", False)
    assert items[1] == ("Setup database", True)
    assert items[2] == ("Fix login issue", False)
    assert items[3] == ("Update dependencies", False)


def test_extract_checkbox_items_empty_content():
    """Test extracting from empty content."""
    items = extract_checkbox_items("")
    assert items == []


def test_extract_checkbox_items_no_checkboxes():
    """Test extracting from content without checkboxes."""
    content = """
# Regular Markdown

Some text here.

- Regular bullet
- Another bullet

No checkboxes at all.
"""
    items = extract_checkbox_items(content)
    assert items == []


def test_extract_checkbox_items_special_characters():
    """Test extracting items with special characters in titles."""
    content = """
- [ ] Fix bug #123
- [x] Update config.json file
- [ ] Add @mentions support
- [ ] Handle "quoted strings"
"""
    items = extract_checkbox_items(content)
    assert len(items) == 4
    assert items[0][0] == "Fix bug #123"
    assert items[1][0] == "Update config.json file"
    assert items[2][0] == "Add @mentions support"
    assert items[3][0] == 'Handle "quoted strings"'


def test_parse_markdown_file_basic(tmp_path):
    """Test parsing a basic markdown file."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
# Tasks

- [ ] Task 1
- [x] Task 2
- [ ] Task 3
""")

    tasks = parse_markdown_file(md_file)
    assert len(tasks) == 3
    assert tasks[0].title == "Task 1"
    assert tasks[0].status == TaskStatus.PENDING
    assert tasks[1].title == "Task 2"
    assert tasks[1].status == TaskStatus.COMPLETED
    assert tasks[1].completed_at is not None
    assert tasks[2].title == "Task 3"
    assert tasks[2].status == TaskStatus.PENDING


def test_parse_markdown_file_generates_unique_ids(tmp_path):
    """Test that parsing generates unique IDs for each task."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
""")

    tasks = parse_markdown_file(md_file)
    ids = [task.id for task in tasks]
    assert len(ids) == len(set(ids))  # All IDs are unique


def test_parse_markdown_file_not_found():
    """Test parsing a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_markdown_file(Path("/non/existent/file.md"))


def test_parse_markdown_file_empty(tmp_path):
    """Test parsing an empty markdown file."""
    md_file = tmp_path / "empty.md"
    md_file.write_text("")

    tasks = parse_markdown_file(md_file)
    assert tasks == []


def test_parse_markdown_file_no_checkboxes(tmp_path):
    """Test parsing a markdown file without checkboxes."""
    md_file = tmp_path / "no_checkboxes.md"
    md_file.write_text("""
# Regular Content

Just some text here.
No checkbox items.
""")

    tasks = parse_markdown_file(md_file)
    assert tasks == []


def test_parse_markdown_file_complex(tmp_path):
    """Test parsing a complex markdown file."""
    md_file = tmp_path / "complex.md"
    md_file.write_text("""
# GitDo Project

## Phase 1 - Setup
- [x] Initialize repository
- [x] Setup project structure
- [ ] Configure CI/CD

## Phase 2 - Core Features
- [ ] Implement task storage
  - [ ] Add JSON persistence
  - [ ] Add file discovery
- [ ] Create CLI interface
  - [x] Add init command
  - [ ] Add list command

## Phase 3 - Advanced
- [ ] Add markdown import
- [ ] Add task filtering
""")

    tasks = parse_markdown_file(md_file)
    assert len(tasks) == 11

    # Check completed tasks
    completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    assert len(completed_tasks) == 3

    # Check pending tasks
    pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
    assert len(pending_tasks) == 8
