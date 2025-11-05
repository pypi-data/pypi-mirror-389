"""CLI interface for GitDo."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .markdown_parser import parse_markdown_file
from .storage import Storage

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """GitDo - Simple CLI tool to plan your work."""
    pass


@cli.command()
def init():
    """Initialize a new GitDo project."""
    # Use current directory explicitly to allow nested projects
    storage = Storage(base_path=Path.cwd())
    if storage.is_initialized():
        console.print("[yellow]GitDo is already initialized in this directory.[/yellow]")
        return

    storage.init()
    console.print("[green]✓[/green] GitDo initialized successfully!")
    console.print(f"[dim]Created .gitdo/ folder in {storage.base_path}[/dim]")


@cli.command()
@click.argument("task")
def add(task: str):
    """Add a new task to your project."""
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    created_task = storage.add_task(task)
    console.print(f"[green]✓[/green] Added task: {created_task.title}")
    console.print(f"[dim]ID: {created_task.id[:8]}[/dim]")


@cli.command()
@click.option(
    "--status",
    "-s",
    type=click.Choice(["pending", "inprogress", "completed"], case_sensitive=False),
    help="Filter tasks by status",
)
@click.option("--all", "-a", is_flag=True, help="Show all tasks (overrides --status)")
def list(status: str | None, all: bool):
    """List all tasks."""
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    tasks = storage.load_tasks()

    # Filter by status if specified
    if not all:
        if status:
            tasks = [t for t in tasks if t.status.value == status.lower()]
        else:
            # Default: show pending and inprogress tasks
            tasks = [t for t in tasks if t.status.value in ["pending", "inprogress"]]

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Sort tasks: inprogress first, then pending, then completed
    status_priority = {"inprogress": 0, "pending": 1, "completed": 2}
    tasks = sorted(tasks, key=lambda t: status_priority.get(t.status.value, 3))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Task")
    table.add_column("Status", width=12)
    table.add_column("Created", width=20)

    for task in tasks:
        # Color coding for different statuses
        if task.status.value == "completed":
            status_color = "green"
        elif task.status.value == "inprogress":
            status_color = "blue"
        else:
            status_color = "yellow"

        table.add_row(
            task.id[:8],
            task.title,
            f"[{status_color}]{task.status.value}[/{status_color}]",
            task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

    console.print(table)


@cli.command()
@click.argument("task_id")
def start(task_id: str):
    """Mark a task as in progress."""
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    if storage.start_task(task_id):
        console.print(f"[green]✓[/green] Task {task_id} marked as in progress!")
    else:
        console.print(f"[red]Error:[/red] Task {task_id} not found.")
        raise click.Abort()


@cli.command()
@click.argument("task_id")
def complete(task_id: str):
    """Mark a task as completed."""
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    if storage.complete_task(task_id):
        console.print(f"[green]✓[/green] Task {task_id} marked as completed!")
    else:
        console.print(f"[red]Error:[/red] Task {task_id} not found.")
        raise click.Abort()


@cli.command()
@click.argument("task_id")
def remove(task_id: str):
    """Remove a task from your project."""
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    if storage.remove_task(task_id):
        console.print(f"[green]✓[/green] Task {task_id} removed!")
    else:
        console.print(f"[red]Error:[/red] Task {task_id} not found.")
        raise click.Abort()


@cli.command("import-md")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--skip-duplicates",
    is_flag=True,
    help="Skip tasks with duplicate titles",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview tasks without importing",
)
def import_md(
    file_path: Path,
    *,
    skip_duplicates: bool,
    dry_run: bool,
) -> None:
    """
    Import tasks from a markdown file.

    Scans for checkbox items in the format:
    - [ ] Task title (pending)
    - [x] Task title (completed)
    """
    storage = Storage()
    if not storage.is_initialized():
        console.print("[red]Error:[/red] GitDo is not initialized. Run 'gitdo init' first.")
        raise click.Abort()

    try:
        tasks = parse_markdown_file(file_path)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise click.Abort() from None
    except PermissionError:
        console.print(f"[red]Error:[/red] Cannot read file: {file_path}")
        raise click.Abort() from None

    if not tasks:
        console.print(f"[yellow]No checkbox items found in {file_path}[/yellow]")
        return

    # Display preview table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Task", style="")
    table.add_column("Status", width=12)

    for task in tasks:
        # Color coding for different statuses
        if task.status.value == "completed":
            status_color = "green"
        elif task.status.value == "inprogress":
            status_color = "blue"
        else:
            status_color = "yellow"

        table.add_row(
            task.title,
            f"[{status_color}]{task.status.value}[/{status_color}]",
        )

    console.print(f"\n[bold]Found {len(tasks)} task(s) in {file_path}:[/bold]")
    console.print(table)

    if dry_run:
        console.print("\n[dim]Dry run - no tasks were imported[/dim]")
        return

    # Import tasks
    imported_count, skipped_count = storage.import_tasks(
        tasks,
        skip_duplicates=skip_duplicates,
    )

    # Display results
    console.print(f"\n[green]✓[/green] Imported {imported_count} task(s)")
    if skipped_count > 0:
        console.print(f"[yellow]⚠[/yellow] Skipped {skipped_count} duplicate(s)")


def main():
    """Entry point for the CLI."""
    cli()
