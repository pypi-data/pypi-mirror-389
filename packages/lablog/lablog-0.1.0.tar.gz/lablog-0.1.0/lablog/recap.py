"""Recap generation for lablog - smart summarization of recent activity."""

from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from rich.console import Console
from rich.table import Table


class RecapGenerator:
    """Generates formatted recaps of lablog entries."""

    def __init__(self):
        self.console = Console()

    def generate_recap(
        self,
        entries: List[Dict[str, Any]],
        days: int = 7,
        todos_only: bool = False
    ):
        """Generate and display a recap."""
        if not entries:
            self.console.print("[yellow]No entries found for the specified period.[/yellow]")
            return

        # Group entries by date
        entries_by_date = self._group_by_date(entries)

        # Display header
        self.console.print(f"\n[bold cyan]🐶 Lablog Recap - Last {days} days[/bold cyan]\n")

        if todos_only:
            self._display_todos(entries)
        else:
            self._display_full_recap(entries_by_date)

    def _group_by_date(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group entries by date."""
        grouped = defaultdict(list)

        for entry in entries:
            date_str = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d")
            grouped[date_str].append(entry)

        return dict(sorted(grouped.items(), reverse=True))

    def _display_full_recap(self, entries_by_date: Dict[str, List[Dict[str, Any]]]):
        """Display full recap grouped by date."""
        for date_str, entries in entries_by_date.items():
            # Parse date for nice formatting
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            days_ago = (datetime.now() - date_obj).days

            if days_ago == 0:
                date_label = "Today"
            elif days_ago == 1:
                date_label = "Yesterday"
            else:
                date_label = f"{days_ago} days ago"

            self.console.print(f"\n[bold blue]{date_label}[/bold blue] ({date_str})")
            self.console.print("─" * 60)

            for entry in entries:
                self._display_entry(entry)

    def _display_entry(self, entry: Dict[str, Any]):
        """Display a single entry with appropriate formatting."""
        entry_type = entry.get("type", "note")
        timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M")

        if entry_type == "experiment":
            self._display_experiment(entry, timestamp)
        elif entry_type == "todo":
            self._display_todo(entry, timestamp)
        elif entry_type == "note":
            self._display_note(entry, timestamp)
        elif entry_type == "code_change":
            self._display_code_change(entry, timestamp)
        else:
            self._display_generic(entry, timestamp)

    def _display_experiment(self, entry: Dict[str, Any], timestamp: str):
        """Display an experiment entry."""
        description = entry.get("description", "No description")

        self.console.print(f"  [green]●[/green] [{timestamp}] [bold]Experiment:[/bold] {description}")

        # Show command if available
        if "command" in entry:
            self.console.print(f"    [dim]→ {entry['command']}[/dim]")

        # Show script summary if available
        if "context" in entry and "script_summary" in entry["context"]:
            summary = entry["context"]["script_summary"]
            if "description" in summary and summary["description"]:
                self.console.print(f"    [dim]Script: {summary['description']}[/dim]")

        # Show git context
        if "context" in entry and "git" in entry["context"]:
            git = entry["context"]["git"]
            branch = git.get("branch", "unknown")
            commit = git.get("commit", "")
            self.console.print(f"    [dim]Branch: {branch} @ {commit}[/dim]")

        self.console.print()

    def _display_todo(self, entry: Dict[str, Any], timestamp: str):
        """Display a todo entry."""
        description = entry.get("description", "No description")
        status = entry.get("status", "pending")
        priority = entry.get("priority", "normal")

        # Choose icon and color based on status
        if status == "completed":
            icon = "✓"
            color = "green"
        elif status == "in_progress":
            icon = "▶"
            color = "yellow"
        else:
            icon = "○"
            color = "white"

        # Priority indicator
        priority_marker = ""
        if priority == "high":
            priority_marker = " [red]![/red]"
        elif priority == "low":
            priority_marker = " [dim](low)[/dim]"

        self.console.print(f"  [{color}]{icon}[/{color}] [{timestamp}] {description}{priority_marker}")

    def _display_note(self, entry: Dict[str, Any], timestamp: str):
        """Display a note entry."""
        description = entry.get("description", "No description")
        self.console.print(f"  [blue]📝[/blue] [{timestamp}] {description}")

    def _display_code_change(self, entry: Dict[str, Any], timestamp: str):
        """Display a code change entry."""
        description = entry.get("description", "No description")
        self.console.print(f"  [magenta]⚡[/magenta] [{timestamp}] [bold]Code change:[/bold] {description}")

        if "files" in entry:
            for file in entry["files"][:3]:  # Show first 3 files
                self.console.print(f"    [dim]→ {file}[/dim]")

    def _display_generic(self, entry: Dict[str, Any], timestamp: str):
        """Display a generic entry."""
        description = entry.get("description", str(entry))
        self.console.print(f"  [white]•[/white] [{timestamp}] {description}")

    def _display_todos(self, entries: List[Dict[str, Any]]):
        """Display only todos in a table format."""
        todos = [e for e in entries if e.get("type") == "todo"]

        if not todos:
            self.console.print("[yellow]No todos found.[/yellow]")
            return

        table = Table(title="Active Todos", show_header=True, header_style="bold cyan")
        table.add_column("Status", style="dim", width=12)
        table.add_column("Priority", width=8)
        table.add_column("Description", overflow="fold")
        table.add_column("Created", style="dim", width=10)

        for todo in todos:
            status = todo.get("status", "pending")
            priority = todo.get("priority", "normal")
            description = todo.get("description", "")
            timestamp = datetime.fromisoformat(todo["timestamp"]).strftime("%Y-%m-%d")

            # Status emoji
            if status == "completed":
                status_text = "✓ Done"
                style = "green"
            elif status == "in_progress":
                status_text = "▶ Working"
                style = "yellow"
            else:
                status_text = "○ Pending"
                style = "white"

            # Priority styling
            if priority == "high":
                priority_text = "[red]HIGH[/red]"
            elif priority == "low":
                priority_text = "[dim]low[/dim]"
            else:
                priority_text = "normal"

            table.add_row(
                f"[{style}]{status_text}[/{style}]",
                priority_text,
                description,
                timestamp
            )

        self.console.print(table)
