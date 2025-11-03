"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner

from gitdo.cli import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_init_command(runner):
    """Test init command."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "initialized successfully" in result.output.lower()


def test_init_already_initialized(runner):
    """Test init command when already initialized."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "already initialized" in result.output.lower()


def test_add_command(runner):
    """Test add command."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["add", "Test task"])
        assert result.exit_code == 0
        assert "added task" in result.output.lower()


def test_add_without_init(runner):
    """Test add command without initialization."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["add", "Test task"])
        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()


def test_list_command(runner):
    """Test list command."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["add", "Task 1"])
        runner.invoke(cli, ["add", "Task 2"])

        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Task 1" in result.output
        assert "Task 2" in result.output


def test_list_empty(runner):
    """Test list command with no tasks."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "no tasks" in result.output.lower()


def test_list_without_init(runner):
    """Test list command without initialization."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["list"])
        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()


def test_complete_command(runner):
    """Test complete command."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        add_result = runner.invoke(cli, ["add", "Test task"])

        # Extract task ID from output (first 8 characters of UUID)
        task_id = add_result.output.split("ID: ")[1].split("\n")[0]

        result = runner.invoke(cli, ["complete", task_id])
        assert result.exit_code == 0
        assert "marked as completed" in result.output.lower()


def test_complete_nonexistent_task(runner):
    """Test complete command with non-existent task."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["complete", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


def test_remove_command(runner):
    """Test remove command."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        add_result = runner.invoke(cli, ["add", "Test task"])

        # Extract task ID from output
        task_id = add_result.output.split("ID: ")[1].split("\n")[0]

        result = runner.invoke(cli, ["remove", task_id])
        assert result.exit_code == 0
        assert "removed" in result.output.lower()


def test_remove_nonexistent_task(runner):
    """Test remove command with non-existent task."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["remove", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


def test_list_all_flag(runner):
    """Test list command with --all flag."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        add_result = runner.invoke(cli, ["add", "Test task"])
        task_id = add_result.output.split("ID: ")[1].split("\n")[0]
        runner.invoke(cli, ["complete", task_id])

        # Without --all, completed tasks should not be shown
        result = runner.invoke(cli, ["list"])
        assert "Test task" not in result.output

        # With --all, completed tasks should be shown
        result = runner.invoke(cli, ["list", "--all"])
        assert "Test task" in result.output
        assert "completed" in result.output.lower()


def test_import_md_basic(runner, tmp_path):
    """Test import-md command with basic markdown file."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
# Tasks

- [ ] Task 1
- [x] Task 2
- [ ] Task 3
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["import-md", str(md_file)])
        assert result.exit_code == 0
        assert "Imported 3 task(s)" in result.output
        assert "Task 1" in result.output
        assert "Task 2" in result.output
        assert "Task 3" in result.output


def test_import_md_without_init(runner, tmp_path):
    """Test import-md command without initialization."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("- [ ] Task 1")

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["import-md", str(md_file)])
        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()


def test_import_md_file_not_found(runner):
    """Test import-md command with non-existent file."""
    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["import-md", "/non/existent/file.md"])
        assert result.exit_code != 0


def test_import_md_no_checkboxes(runner, tmp_path):
    """Test import-md command with file without checkboxes."""
    md_file = tmp_path / "no_tasks.md"
    md_file.write_text("""
# Just some text

No checkbox items here.
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["import-md", str(md_file)])
        assert result.exit_code == 0
        assert "No checkbox items found" in result.output


def test_import_md_skip_duplicates(runner, tmp_path):
    """Test import-md command with --skip-duplicates flag."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
- [ ] Duplicate task
- [ ] Unique task
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        # Add a task manually first
        runner.invoke(cli, ["add", "Duplicate task"])

        # Import with skip-duplicates
        result = runner.invoke(cli, ["import-md", str(md_file), "--skip-duplicates"])
        assert result.exit_code == 0
        assert "Imported 1 task(s)" in result.output
        assert "Skipped 1 duplicate(s)" in result.output


def test_import_md_dry_run(runner, tmp_path):
    """Test import-md command with --dry-run flag."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
- [ ] Task 1
- [ ] Task 2
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["import-md", str(md_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Task 1" in result.output
        assert "Task 2" in result.output
        assert "Dry run - no tasks were imported" in result.output

        # Verify tasks were not actually imported
        list_result = runner.invoke(cli, ["list"])
        assert "No tasks found" in list_result.output


def test_import_md_complex_file(runner, tmp_path):
    """Test import-md with complex markdown file."""
    md_file = tmp_path / "complex.md"
    md_file.write_text("""
# Project Tasks

## Phase 1
- [x] Setup project
- [ ] Write docs

## Phase 2
- [ ] Implement feature A
  - [ ] Sub-task 1
  - [ ] Sub-task 2
- [ ] Implement feature B

Some random text here.

## Phase 3
- [ ] Deploy to production
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["import-md", str(md_file)])
        assert result.exit_code == 0
        assert "Imported 7 task(s)" in result.output

        # Verify tasks are in storage
        list_result = runner.invoke(cli, ["list", "--all"])
        assert "Setup project" in list_result.output
        assert "Write docs" in list_result.output
        assert "Deploy to production" in list_result.output


def test_import_md_preserves_status(runner, tmp_path):
    """Test that import-md preserves task status (completed vs pending)."""
    md_file = tmp_path / "tasks.md"
    md_file.write_text("""
- [ ] Pending task
- [x] Completed task
- [X] Another completed task
""")

    with runner.isolated_filesystem():
        runner.invoke(cli, ["init"])
        runner.invoke(cli, ["import-md", str(md_file)])

        # Check that completed tasks show up in --all but not in default list
        default_list = runner.invoke(cli, ["list"])
        all_list = runner.invoke(cli, ["list", "--all"])

        assert "Pending task" in default_list.output
        assert "Completed task" not in default_list.output
        assert "Another completed task" not in default_list.output

        assert "Pending task" in all_list.output
        assert "Completed task" in all_list.output
        assert "Another completed task" in all_list.output
