"""Terminal UI for interactive todo management."""

from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


def interactive_todo_list(todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Display interactive todo list and allow marking as done.

    Args:
        todos: List of todo entries

    Returns:
        Updated list of todos with modified statuses
    """
    if not todos:
        console.print("[yellow]No todos found.[/yellow]")
        return []

    # Filter only pending todos
    pending_todos = [t for t in todos if t.get("status") != "completed"]

    if not pending_todos:
        console.print("[green]All todos completed![/green]")
        return todos

    console.print("\n[bold cyan]Interactive Todo List[/bold cyan]\n")

    # Display todos with numbers
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Status", width=10)
    table.add_column("Priority", width=8)
    table.add_column("Description")

    for idx, todo in enumerate(pending_todos, 1):
        status = todo.get("status", "pending")
        priority = todo.get("priority", "normal")
        description = todo.get("description", "")

        # Status icon
        if status == "completed":
            status_text = "[green]✓ Done[/green]"
        elif status == "in_progress":
            status_text = "[yellow]▶ Working[/yellow]"
        else:
            status_text = "[white]○ Pending[/white]"

        # Priority styling
        if priority == "high":
            priority_text = "[red]HIGH[/red]"
        elif priority == "low":
            priority_text = "[dim]low[/dim]"
        else:
            priority_text = "normal"

        table.add_row(str(idx), status_text, priority_text, description)

    console.print(table)

    console.print("\n[dim]Commands: Enter todo number to toggle done, 'q' to quit, 'a' to mark all done[/dim]\n")

    # Track changes
    modified = []

    while True:
        choice = Prompt.ask("Select todo (or 'q' to quit)").strip().lower()

        if choice == 'q':
            break
        elif choice == 'a':
            if Confirm.ask("Mark all todos as completed?"):
                for todo in pending_todos:
                    todo["status"] = "completed"
                    modified.append(todo)
                console.print("[green]✓ All todos marked as completed[/green]")
                break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(pending_todos):
                todo = pending_todos[idx]
                current_status = todo.get("status", "pending")

                if current_status == "completed":
                    todo["status"] = "pending"
                    console.print(f"[yellow]Todo {idx+1} marked as pending[/yellow]")
                else:
                    todo["status"] = "completed"
                    console.print(f"[green]✓ Todo {idx+1} marked as completed[/green]")

                modified.append(todo)
            else:
                console.print("[red]Invalid todo number[/red]")
        else:
            console.print("[red]Invalid input. Enter a number, 'a', or 'q'.[/red]")

    return modified


def display_todo_summary(todos: List[Dict[str, Any]]):
    """
    Display a summary of todos grouped by status.

    Args:
        todos: List of todo entries
    """
    if not todos:
        console.print("[yellow]No todos found.[/yellow]")
        return

    # Group by status
    pending = [t for t in todos if t.get("status") == "pending"]
    in_progress = [t for t in todos if t.get("status") == "in_progress"]
    completed = [t for t in todos if t.get("status") == "completed"]

    console.print("\n[bold cyan]Todo Summary[/bold cyan]\n")

    if pending:
        console.print(f"[yellow]⚬ Pending:[/yellow] {len(pending)}")
        for todo in pending[:5]:  # Show first 5
            desc = todo.get("description", "")[:60]
            priority = todo.get("priority", "normal")
            priority_marker = " [red]![/red]" if priority == "high" else ""
            console.print(f"  • {desc}{priority_marker}")
        if len(pending) > 5:
            console.print(f"  [dim]...and {len(pending) - 5} more[/dim]")
        console.print()

    if in_progress:
        console.print(f"[cyan]▶ In Progress:[/cyan] {len(in_progress)}")
        for todo in in_progress:
            desc = todo.get("description", "")[:60]
            console.print(f"  • {desc}")
        console.print()

    if completed:
        console.print(f"[green]✓ Completed:[/green] {len(completed)}")

    console.print()
