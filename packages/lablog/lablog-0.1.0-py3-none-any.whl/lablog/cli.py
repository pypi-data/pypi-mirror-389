"""Command-line interface for lablog."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt

from .storage import LablogStorage
from .context import ContextDetector
from .analyzer import ScriptAnalyzer
from .recap import RecapGenerator
from .claude_integration import ClaudeCodeIntegration
from .config import LablogConfig
from .job_utils import extract_output_file_from_script, check_job_status
from .tui import interactive_todo_list

console = Console()


# Helper functions to reduce boilerplate
def get_context():
    """Get common objects used by most commands."""
    return {
        'storage': LablogStorage(),
        'detector': ContextDetector(),
        'config': LablogConfig(),
    }


def get_end_of_day(date_str: str) -> datetime:
    """Convert YYYY-MM-DD string to end of that day (23:59:59)."""
    return datetime.fromisoformat(date_str).replace(hour=23, minute=59, second=59)


def show_entry_preview(entries: list, max_display: int = 10):
    """Display a preview of entries."""
    console.print(f"\nFound {len(entries)} entries:")
    for entry in entries[:max_display]:
        timestamp = entry["timestamp"][:16]
        entry_type = entry.get("type", "note")
        desc = entry.get("description", "")[:60]
        console.print(f"  [{timestamp}] {entry_type}: {desc}")
    if len(entries) > max_display:
        console.print(f"  [dim]...and {len(entries) - max_display} more[/dim]")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", is_flag=True, help="Show version and exit")
def cli(ctx, version):
    """🐶 lablog - Research workflow memory system.

    Track experiments, todos, and context across projects.
    """
    if version:
        from . import __version__
        console.print(f"lablog version {__version__} 🐶")
        ctx.exit()

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@cli.command()
@click.argument("description", required=False)
@click.argument("command", nargs=-1)
@click.option("--type", "entry_type", default="note", help="Entry type (note, experiment, todo)")
@click.option("--priority", default="normal", help="Priority (low, normal, high)")
def log(description: Optional[str], command: tuple, entry_type: str, priority: str):
    """Log an entry with optional command execution.

    Examples:
        lablog log "Testing new architecture" sbatch jobs/train.sh
        lablog log "Found interesting bug in data loader"
        lablog log --type todo "Implement attention mechanism"
        sbatch jobs/train.sh  # When using hooks, description is optional
    """
    storage = LablogStorage()
    detector = ContextDetector()
    analyzer = ScriptAnalyzer()
    config = LablogConfig()

    # Get project context
    project_root = detector.get_git_root()
    git_context = detector.get_git_context()

    # Fix argument parsing: if description looks like a command and command exists,
    # treat description as part of the command
    if description and command and description.lower() in ['sbatch', 'python', 'bash', 'sh', 'srun']:
        command = (description,) + command
        description = None

    # Check if this is a job command (sbatch) - do this early
    is_job = command and "sbatch" in command[0].lower()

    # Build entry (description will be set later for jobs if needed)
    entry = {
        "type": entry_type,
        "description": description or "",  # Will be filled in later if empty
    }

    if priority != "normal":
        entry["priority"] = priority

    # Add git context
    if git_context:
        entry["context"] = {"git": git_context}

    # Track if command succeeded (defaults to True if no command)
    command_succeeded = True
    script_path = None

    # If command is provided, execute it and analyze
    if command:
        command_str = " ".join(command)
        entry["command"] = command_str

        # Analyze script if it's a file reference
        script_analysis = _analyze_command_for_scripts(command, analyzer)
        script_path = _extract_script_path_from_command(command)

        if script_analysis:
            if "context" not in entry:
                entry["context"] = {}
            entry["context"]["script_summary"] = script_analysis

        # For jobs, extract output file
        if is_job and script_path:
            entry["script_path"] = str(script_path)
            output_file = extract_output_file_from_script(script_path)
            if output_file:
                entry["output_file"] = output_file

        # Use Claude for AI summary if enabled
        if config.is_claude_enabled():
            if script_path:
                claude = ClaudeCodeIntegration()
                ai_analysis = claude.summarize_script(script_path)
                if ai_analysis:
                    if "context" not in entry:
                        entry["context"] = {}
                    entry["context"]["ai_summary"] = ai_analysis

        # Execute command
        console.print(f"[blue]Executing:[/blue] {command_str}")
        try:
            result = subprocess.run(
                command,
                cwd=detector.working_dir,
                capture_output=True,
                text=True
            )

            # Store command output/result
            entry["command_result"] = {
                "returncode": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",  # Truncate
                "stderr": result.stderr[:500] if result.stderr else "",
            }

            # Print output
            if result.stdout:
                console.print(result.stdout, end="")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]", end="")

            if result.returncode != 0:
                console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
                command_succeeded = False

        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")
            entry["command_error"] = str(e)
            command_succeeded = False

    # Only save entry if command succeeded (or no command was run)
    if not command_succeeded:
        return

    # For jobs with no description, use AI summary or script name
    if is_job and not entry["description"]:
        if entry.get("context", {}).get("ai_summary", {}).get("summary"):
            # Use AI summary as description
            entry["description"] = entry["context"]["ai_summary"]["summary"]
        elif script_path:
            # Use script name as fallback
            entry["description"] = f"Job: {script_path.name}"
        else:
            # Last resort: use command
            entry["description"] = " ".join(command)

    # Ensure description is not empty for non-jobs
    if not is_job and not entry["description"]:
        entry["description"] = " ".join(command) if command else "Logged entry"

    # Save entry (to jobs.jsonl if it's a job, otherwise to log.jsonl)
    if is_job:
        storage.append_job_entry(entry, project_root)
        console.print(f"[green]✓ Job logged:[/green] {entry['description'][:80]}")
    else:
        storage.append_entry(entry, project_root)
        console.print(f"[green]✓ Logged:[/green] {entry['description'][:80]}")


@cli.command()
@click.argument("message", required=False)
@click.option("--priority", default="normal", help="Priority (low, normal, high)")
@click.option("-l", "--list", "show_list", is_flag=True, help="Show interactive todo list")
@click.option("-r", "--raw", is_flag=True, help="Skip AI enhancement")
def todo(message: Optional[str], priority: str, show_list: bool, raw: bool):
    """Add a todo item or show interactive list.

    Examples:
        lablog todo "Implement attention mechanism"
        lablog todo "Fix memory leak" --priority high
        lablog todo -l  # Interactive list
        lablog todo "Quick note" -r  # Skip AI enhancement
    """
    storage = LablogStorage()
    detector = ContextDetector()
    config = LablogConfig()

    project_root = detector.get_git_root()

    # Show interactive list if -l flag
    if show_list:
        # Read all todos
        todos = storage.read_entries(project_root=project_root, entry_type="todo")

        if not todos:
            console.print("[yellow]No todos found.[/yellow]")
            return

        # Show interactive list
        modified_todos = interactive_todo_list(todos)

        # Update modified todos in storage
        for todo in modified_todos:
            storage.update_entry(
                timestamp=todo["timestamp"],
                updates={"status": todo["status"]},
                project_root=project_root,
                is_job=False
            )

        console.print(f"\n[green]✓ Updated {len(modified_todos)} todo(s)[/green]")
        return

    # Add new todo if message provided
    if not message:
        console.print("[red]Error: Message required when not using --list[/red]")
        console.print("Use [cyan]lablog todo -l[/cyan] to show interactive list")
        return

    git_context = detector.get_git_context()

    # Enhance todo with Claude if enabled and not raw
    enhanced_message = message
    if config.is_claude_enabled() and not raw:
        claude = ClaudeCodeIntegration()
        enhanced = claude.enhance_todo(message)
        if enhanced:
            enhanced_message = enhanced
            console.print(f"[dim]Enhanced: {enhanced_message}[/dim]")

    entry = {
        "type": "todo",
        "description": enhanced_message,
        "status": "pending",
    }

    if priority != "normal":
        entry["priority"] = priority

    if git_context:
        entry["context"] = {"git": git_context}

    storage.append_entry(entry, project_root)

    priority_marker = ""
    if priority == "high":
        priority_marker = " [red](HIGH)[/red]"
    elif priority == "low":
        priority_marker = " [dim](low)[/dim]"

    console.print(f"[green]🐶 Todo added:[/green] {enhanced_message}{priority_marker}")


@cli.command()
@click.argument("message")
@click.option("-r", "--raw", is_flag=True, help="Skip AI enhancement")
def note(message: str, raw: bool):
    """Add a note/observation.

    Examples:
        lablog note "Baseline model achieving 0.85 AUROC"
        lablog note "Quick observation" -r  # Skip AI enhancement
    """
    ctx = get_context()
    storage, detector, config = ctx['storage'], ctx['detector'], ctx['config']

    project_root = detector.get_git_root()
    git_context = detector.get_git_context()

    # Enhance note with Claude if enabled and not raw
    enhanced_message = message
    if config.is_claude_enabled() and not raw:
        claude = ClaudeCodeIntegration()
        enhanced = claude.enhance_note(message)
        if enhanced:
            enhanced_message = enhanced
            console.print(f"[dim]Enhanced: {enhanced_message}[/dim]")

    entry = {
        "type": "note",
        "description": enhanced_message,
    }

    if git_context:
        entry["context"] = {"git": git_context}

    storage.append_entry(entry, project_root)

    console.print(f"[green]🐶 Note added:[/green] {enhanced_message}")


@cli.command()
@click.option("--days", default=7, help="Number of days to show")
@click.option("--todos-only", is_flag=True, help="Show only todos")
@click.option("--all-projects", is_flag=True, help="Show entries from all projects")
def recap(days: int, todos_only: bool, all_projects: bool):
    """Show a recap of recent activity (always AI-enhanced if Claude is enabled).

    Examples:
        lablog recap
        lablog recap --days 14
        lablog recap --todos-only
    """
    storage = LablogStorage()
    detector = ContextDetector()
    generator = RecapGenerator()
    config = LablogConfig()

    # Determine which project to show
    project_root = None if all_projects else detector.get_git_root()

    # Read entries and jobs
    entries = storage.read_entries(project_root=project_root, days=days)
    job_entries = []
    if not todos_only and project_root:
        job_entries = storage.read_job_entries(project_root=project_root)

    # Only show recap if there are entries OR jobs
    if not entries and not job_entries:
        console.print(f"\n[yellow]No activity found in the last {days} days.[/yellow]\n")
        return

    # Generate basic recap (only if there are regular entries)
    if entries:
        generator.generate_recap(entries, days=days, todos_only=todos_only)
    elif job_entries and not todos_only:
        # Only jobs, no regular entries - show header
        console.print(f"\n[bold cyan]🐶 Lablog Recap - Last {days} days[/bold cyan]\n")
        console.print("[dim]No notes or todos in this period, but found jobs below.[/dim]\n")

    # Always enhance recap with Claude if enabled
    if config.is_claude_enabled() and entries and not todos_only:
        console.print("\n[bold magenta]AI-Enhanced Insights[/bold magenta]\n")
        claude = ClaudeCodeIntegration()
        enhanced_summary = claude.enhance_recap(entries, days, job_entries=job_entries)
        if enhanced_summary:
            console.print(enhanced_summary)
            console.print()

    # Show job status summary (if jobs exist and not todos-only view)
    if not todos_only and project_root and job_entries:
        console.print("\n" + "─" * 60)
        console.print("[bold cyan]Job Status Summary[/bold cyan]\n")

        # Check status of each job
        job_statuses = []
        for job in job_entries:
            status = check_job_status(job)
            job_statuses.append((job, status))

        # Deduplicate jobs with same output file - only analyze the most recent
        output_file_groups = {}
        for job, status in job_statuses:
            if status.get("status") == "found" and status.get("needs_analysis"):
                output_file = status.get("output_file")
                if output_file:
                    if output_file not in output_file_groups:
                        output_file_groups[output_file] = []
                    output_file_groups[output_file].append((job, status))

        # For each output file with multiple jobs, mark older ones as superseded
        for output_file, jobs_with_status in output_file_groups.items():
            if len(jobs_with_status) > 1:
                # Sort by timestamp (newest first)
                jobs_with_status.sort(key=lambda x: x[0].get("timestamp", ""), reverse=True)

                # Keep the newest, mark others as superseded
                for job, status in jobs_with_status[1:]:
                    status["status"] = "superseded"
                    status["needs_analysis"] = False
                    status["message"] = "Output file superseded by newer job run"

        # Display summary
        found_count = 0
        for job, status in job_statuses:
            desc = job.get("description", "Unknown job")[:50]
            timestamp = job.get("timestamp", "")[:10]  # YYYY-MM-DD
            status_type = status.get("status")

            if status_type == "found":
                icon = "[green]✓[/green]"
                msg = f"[{timestamp}] {desc} → {status['output_file'].split('/')[-1]} (output exists, recent)"
                found_count += 1
            elif status_type == "superseded":
                icon = "[dim]⊗[/dim]"
                msg = f"[{timestamp}] {desc} → {status['output_file'].split('/')[-1]} [dim](superseded by newer run)[/dim]"
            elif status_type == "not_found":
                icon = "[yellow]⏳[/yellow]"
                msg = f"[{timestamp}] {desc} → {status['output_file'].split('/')[-1]} (no output yet)"
            elif status_type == "old_file":
                icon = "[red]✗[/red]"
                msg = f"[{timestamp}] {desc} → {status['output_file'].split('/')[-1]} (output file older than entry)"
            elif status_type == "no_output":
                icon = "[dim]○[/dim]"
                msg = f"[{timestamp}] {desc} (no output file specified)"
            else:
                icon = "[red]![/red]"
                msg = f"[{timestamp}] {desc} (error: {status.get('message', 'unknown')})"

            console.print(f"  {icon} {msg}")

        # Offer to analyze outputs if Claude enabled and we have recent outputs
        if found_count > 0 and config.is_claude_enabled():
            console.print()
            if click.confirm("Analyze job outputs with Claude?", default=False):
                console.print()
                claude = ClaudeCodeIntegration()

                for job, status in job_statuses:
                    if status.get("status") == "found" and status.get("needs_analysis"):
                        output_file = Path(status["output_file"])
                        analysis = claude.analyze_job_output(output_file)

                        if analysis and analysis.get("status") == "analyzed":
                            console.print(f"\n[bold cyan]{job.get('script_path', 'Unknown').split('/')[-1]}:[/bold cyan]")
                            console.print(analysis["analysis"])

        console.print()


@cli.command()
@click.option("--days", default=7, help="Number of days to show")
@click.option("--todos-only", is_flag=True, help="Show only todos")
@click.option("--all-projects", is_flag=True, help="Show entries from all projects")
def status(days: int, todos_only: bool, all_projects: bool):
    """Show recent activity without AI summary (faster).

    Examples:
        lablog status
        lablog status --days 14
        lablog status --todos-only
    """
    storage = LablogStorage()
    detector = ContextDetector()
    generator = RecapGenerator()

    # Determine which project to show
    project_root = None if all_projects else detector.get_git_root()

    # Read entries
    entries = storage.read_entries(project_root=project_root, days=days)

    # Generate basic recap (no AI)
    generator.generate_recap(entries, days=days, todos_only=todos_only)


@cli.command()
def init():
    """Initialize lablog with interactive setup.

    This creates the necessary configuration and optionally sets up Claude Code integration and shell hooks.
    """
    detector = ContextDetector()
    storage = LablogStorage()
    config = LablogConfig()
    claude = ClaudeCodeIntegration()

    console.print("\n[bold cyan]🐶 Initializing lablog[/bold cyan]\n")

    # Check if we're in a git repo
    if detector.is_git_repo():
        git_root = detector.get_git_root()
        console.print(f"[green]✓[/green] Git repository detected: {git_root}")
    else:
        console.print("[yellow]⚠[/yellow] Not in a git repository (optional)")

    # Create storage
    console.print(f"[green]✓[/green] Storage location: {storage.config_dir}")

    # Ask about Claude Code integration
    console.print("\n[bold]Claude Code Integration[/bold]")
    console.print("Claude Code enables AI-powered features:")
    console.print("  • Auto-enhance notes and todos")
    console.print("  • Summarize scripts automatically")
    console.print("  • AI-powered recaps\n")

    if claude.claude_available:
        console.print("[green]✓[/green] Claude Code CLI detected")
        enable_claude = click.confirm("Enable Claude Code integration?", default=True)
        if enable_claude:
            config.enable_claude()
            console.print("[green]✓[/green] Claude Code integration enabled")
        else:
            config.disable_claude()
            console.print("[dim]Claude Code integration disabled[/dim]")
    else:
        console.print("[yellow]⚠[/yellow] Claude Code CLI not found")
        console.print("[dim]Install Claude Code to enable AI features: https://claude.com/claude-code[/dim]")
        config.disable_claude()

    # Ask about shell hooks
    console.print("\n[bold]Shell Hooks (Auto-logging)[/bold]")
    console.print("Shell hooks automatically log commands like sbatch and git commit.\n")

    setup_hooks = click.confirm("Set up shell hooks?", default=True)
    if setup_hooks:
        # Detect shell
        shell = _detect_shell()
        console.print(f"[dim]Detected shell: {shell}[/dim]")

        # Ask which commands to wrap
        console.print("\n[cyan]Which commands would you like to auto-log?[/cyan]")
        wrap_sbatch = click.confirm("  • sbatch (SLURM jobs)", default=True)
        wrap_git = click.confirm("  • git commit", default=True)

        commands = []
        if wrap_sbatch:
            commands.append("sbatch")
        if wrap_git:
            commands.append("git")

        if commands:
            # Generate wrappers
            wrapper_content = _generate_wrapper_content(commands, shell)
            wrapper_file = Path.home() / f".lablog_wrappers.{shell}"
            wrapper_file.write_text(wrapper_content)

            # Determine rc file
            rc_file = Path.home() / f".{shell}rc"

            console.print(f"\n[green]✓[/green] Wrappers written to: {wrapper_file}")
            console.print(f"\n[bold]To activate hooks, add this line to your {rc_file}:[/bold]")
            console.print(f"[cyan]  source {wrapper_file}[/cyan]\n")

            auto_add = click.confirm(f"Automatically add to {rc_file}?", default=False)
            if auto_add:
                # Check if already sourced
                if rc_file.exists():
                    rc_content = rc_file.read_text()
                    if str(wrapper_file) not in rc_content:
                        with open(rc_file, "a") as f:
                            f.write(f"\n# lablog shell hooks\nsource {wrapper_file}\n")
                        console.print(f"[green]✓[/green] Added to {rc_file}")
                        console.print("[yellow]⚠[/yellow] Run [cyan]source {rc_file}[/cyan] or restart your shell to activate")
                    else:
                        console.print("[dim]Already in {rc_file}[/dim]")
                else:
                    console.print(f"[yellow]⚠[/yellow] {rc_file} not found, please add manually")

            config.enable_hooks()
        else:
            console.print("[dim]No commands selected for auto-logging[/dim]")
            config.disable_hooks()
    else:
        console.print("[dim]Shell hooks disabled[/dim]")
        config.disable_hooks()

    # Test write
    test_entry = {
        "type": "note",
        "description": "lablog initialized"
    }
    storage.append_entry(test_entry, detector.get_git_root())

    console.print("\n[bold green]🐶 lablog is ready![/bold green]\n")
    console.print("[bold]Quick start:[/bold]")
    console.print("  • [cyan]lablog log 'Your message'[/cyan] - Log a note")
    console.print("  • [cyan]lablog todo 'Task description'[/cyan] - Add a todo")
    console.print("  • [cyan]lablog recap[/cyan] - View recent activity")
    console.print("  • [cyan]lablog summarize <script>[/cyan] - AI-analyze a script")
    console.print("\n[dim]For more commands: lablog --help[/dim]\n")


@cli.command()
def projects():
    """List all tracked projects."""
    storage = LablogStorage()
    all_projects = storage.get_all_projects()

    if not all_projects:
        console.print("[yellow]No projects tracked yet.[/yellow]")
        return

    console.print(f"\n[bold cyan]🐶 Tracked Projects ({len(all_projects)})[/bold cyan]\n")

    for project in all_projects:
        console.print(f"[green]●[/green] {project['project_root']}")
        console.print(f"  [dim]ID: {project['project_id']}[/dim]")
        console.print(f"  [dim]Created: {project['created_at'][:10]}[/dim]\n")


@cli.command()
@click.option("--from-date", "from_date", help="Start date (YYYY-MM-DD)")
@click.option("--to-date", "to_date", help="End date (YYYY-MM-DD)")
@click.option("--exclude-todos", is_flag=True, help="Exclude todos from merge")
def merge(from_date: Optional[str], to_date: Optional[str], exclude_todos: bool):
    """Merge entries from a date range into a summary.

    Examples:
        lablog merge --from-date 2025-10-01 --to-date 2025-10-31
        lablog merge --exclude-todos
    """
    storage = LablogStorage()
    detector = ContextDetector()
    config = LablogConfig()
    claude = ClaudeCodeIntegration()

    project_root = detector.get_git_root()

    # Prompt for date range if not provided
    if not from_date:
        from_date = Prompt.ask("From date (YYYY-MM-DD or 'all')", default="all")
    if not to_date and from_date != "all":
        to_date = Prompt.ask("To date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))

    # Read entries
    all_entries = storage.read_entries(project_root=project_root)

    # Filter by date range
    if from_date != "all":
        from_dt = datetime.fromisoformat(from_date)
        to_dt = get_end_of_day(to_date) if to_date else datetime.now()

        entries_to_merge = [
            e for e in all_entries
            if from_dt <= datetime.fromisoformat(e["timestamp"]) <= to_dt
        ]
    else:
        entries_to_merge = all_entries
        from_date = entries_to_merge[0]["timestamp"][:10] if entries_to_merge else ""
        to_date = entries_to_merge[-1]["timestamp"][:10] if entries_to_merge else ""

    # Exclude todos if requested
    if exclude_todos:
        entries_to_merge = [e for e in entries_to_merge if e.get("type") != "todo"]

    if not entries_to_merge:
        console.print("[yellow]No entries found in date range.[/yellow]")
        return

    # Show preview
    console.print(f"[bold]Entries to merge:[/bold]")
    show_entry_preview(entries_to_merge)

    # Confirm
    console.print()
    if not click.confirm("Merge these into one summary?", default=False):
        console.print("[yellow]Merge cancelled.[/yellow]")
        return

    # Merge with Claude
    if not config.is_claude_enabled():
        console.print("[yellow]Claude Code not enabled. Run 'lablog init' to enable.[/yellow]")
        return

    merged_summary = claude.merge_entries(entries_to_merge, from_date, to_date)

    if not merged_summary:
        console.print("[red]Failed to merge entries.[/red]")
        return

    # Create merged entry
    merged_entry = {
        "type": "note",
        "description": f"Summary of work from {from_date} to {to_date}: {merged_summary}",
    }

    storage.append_entry(merged_entry, project_root)

    # Archive original entries
    storage.archive_entries(entries_to_merge, project_root, reason="merged")

    console.print(f"\n[green]✓ Created merged entry[/green]")
    console.print(f"[green]✓ Archived {len(entries_to_merge)} original entries[/green]")


@cli.command()
@click.option("--completed-todos-only", is_flag=True, help="Clear only completed todos")
def clear(completed_todos_only: bool):
    """Archive entries to keep active log clean.

    Examples:
        lablog clear  # Interactive mode
        lablog clear --completed-todos-only
    """
    storage = LablogStorage()
    detector = ContextDetector()

    project_root = detector.get_git_root()

    if completed_todos_only:
        # Get all entries
        all_entries = storage.read_entries(project_root=project_root)
        entries_to_clear = [
            e for e in all_entries
            if e.get("type") == "todo" and e.get("status") == "completed"
        ]

        if not entries_to_clear:
            console.print("[yellow]No completed todos found.[/yellow]")
            return

    else:
        # Interactive mode
        console.print("\n[bold cyan]What would you like to clear?[/bold cyan]\n")
        console.print("1. Date range (notes & todos)")
        console.print("2. Before date (notes & todos)")
        console.print("3. Completed todos only")
        console.print("4. Jobs by date range")
        console.print("5. All jobs")
        console.print("6. All entries (dangerous!)")

        choice = Prompt.ask("\nYour choice", choices=["1", "2", "3", "4", "5", "6"])

        all_entries = storage.read_entries(project_root=project_root)

        if choice == "1":
            from_date = Prompt.ask("From date (YYYY-MM-DD)")
            to_date = Prompt.ask("To date (YYYY-MM-DD)")
            from_dt = datetime.fromisoformat(from_date)
            to_dt = get_end_of_day(to_date)
            entries_to_clear = [
                e for e in all_entries
                if from_dt <= datetime.fromisoformat(e["timestamp"]) <= to_dt
            ]
        elif choice == "2":
            before_date = Prompt.ask("Before date (YYYY-MM-DD)")
            before_dt = datetime.fromisoformat(before_date)
            entries_to_clear = [
                e for e in all_entries
                if datetime.fromisoformat(e["timestamp"]) < before_dt
            ]
        elif choice == "3":
            entries_to_clear = [
                e for e in all_entries
                if e.get("type") == "todo" and e.get("status") == "completed"
            ]
        elif choice == "4":
            # Clear jobs by date range
            all_jobs = storage.read_job_entries(project_root=project_root)
            from_date = Prompt.ask("From date (YYYY-MM-DD)")
            to_date = Prompt.ask("To date (YYYY-MM-DD)")
            from_dt = datetime.fromisoformat(from_date)
            to_dt = get_end_of_day(to_date)
            entries_to_clear = [
                j for j in all_jobs
                if from_dt <= datetime.fromisoformat(j["timestamp"]) <= to_dt
            ]
        elif choice == "5":
            # Clear all jobs
            entries_to_clear = storage.read_job_entries(project_root=project_root)
        else:  # choice == "6"
            entries_to_clear = all_entries

    if not entries_to_clear:
        console.print("[yellow]No entries match criteria.[/yellow]")
        return

    # Show preview
    show_entry_preview(entries_to_clear)

    # Confirm
    console.print()
    if not click.confirm("Archive these entries?", default=False):
        console.print("[yellow]Clear cancelled.[/yellow]")
        return

    # Archive
    storage.archive_entries(entries_to_clear, project_root, reason="manual_clear")
    console.print(f"\n[green]✓ Archived {len(entries_to_clear)} entries[/green]")


@cli.command(name="delete-archive")
@click.option("--before-date", "before_date", help="Delete archived entries before this date (YYYY-MM-DD)")
def delete_archive(before_date: Optional[str]):
    """Permanently delete archived entries (DANGEROUS!).

    Examples:
        lablog delete-archive --before-date 2025-09-01
    """
    storage = LablogStorage()
    detector = ContextDetector()

    project_root = detector.get_git_root()

    # Read archived entries
    archived_entries = storage.read_archive_entries(project_root=project_root)

    if not archived_entries:
        console.print("[yellow]No archived entries found.[/yellow]")
        return

    # Filter by date if provided
    if before_date:
        before_dt = datetime.fromisoformat(before_date)
        entries_to_delete = [
            e for e in archived_entries
            if datetime.fromisoformat(e["timestamp"]) < before_dt
        ]
    else:
        # Prompt for date
        before_date = Prompt.ask("Delete archived entries before date (YYYY-MM-DD or 'all')")

        if before_date == "all":
            entries_to_delete = archived_entries
        else:
            before_dt = datetime.fromisoformat(before_date)
            entries_to_delete = [
                e for e in archived_entries
                if datetime.fromisoformat(e["timestamp"]) < before_dt
            ]

    if not entries_to_delete:
        console.print("[yellow]No archived entries match criteria.[/yellow]")
        return

    # Show preview
    console.print(f"\n[red]WARNING: Found {len(entries_to_delete)} archived entries to PERMANENTLY DELETE:[/red]")
    show_entry_preview(entries_to_delete)

    # Require typing DELETE
    console.print("\n[bold red]⚠️  WARNING: This will PERMANENTLY delete these entries![/bold red]")
    confirmation = Prompt.ask("Type 'DELETE' to confirm")

    if confirmation != "DELETE":
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return

    # Delete
    storage.delete_archive_entries(entries_to_delete, project_root)
    console.print(f"\n[green]✓ Permanently deleted {len(entries_to_delete)} archived entries[/green]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
def summarize(script_path: str):
    """Use Claude to summarize a script file.

    Examples:
        lablog summarize jobs/train.sh
        lablog summarize clique_prediction/models/main.py
    """
    claude = ClaudeCodeIntegration()
    path = Path(script_path)

    result = claude.summarize_script(path)

    if result and "summary" in result:
        console.print("\n[bold cyan]AI Summary[/bold cyan]\n")
        console.print(result["summary"])
        console.print()
    elif result and "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")


@cli.command(name="analyze-diff")
def analyze_diff():
    """Use Claude to analyze your uncommitted git changes.

    Examples:
        lablog analyze-diff
    """
    claude = ClaudeCodeIntegration()
    detector = ContextDetector()

    result = claude.analyze_git_diff(detector.working_dir)

    if result and "analysis" in result:
        console.print("\n[bold cyan]AI Analysis of Changes[/bold cyan]\n")
        console.print(result["analysis"])
        console.print()


@cli.command(name="generate-wrappers")
@click.option("--shell", type=click.Choice(["bash", "zsh", "both"]), default="bash", help="Shell type")
@click.option("--commands", default="sbatch,git", help="Comma-separated commands to wrap")
@click.option("--output", type=click.Path(), help="Output file (default: stdout)")
def generate_wrappers(shell: str, commands: str, output: Optional[str]):
    """Generate shell function wrappers for auto-logging.

    Examples:
        lablog generate-wrappers --shell bash --commands sbatch,git
        lablog generate-wrappers --shell zsh --output ~/.lablog_wrappers.sh
    """
    command_list = [cmd.strip() for cmd in commands.split(",")]

    wrapper_content = _generate_wrapper_content(command_list, shell)

    if output:
        output_path = Path(output)
        output_path.write_text(wrapper_content)
        console.print(f"[green]✓ Wrappers written to:[/green] {output_path}")
        console.print(f"\n[cyan]Add to your ~/{'.bashrc' if shell != 'zsh' else '.zshrc'}:[/cyan]")
        console.print(f"  source {output_path}")
    else:
        console.print(wrapper_content)


def _generate_wrapper_content(commands: list, shell: str) -> str:
    """Generate shell wrapper functions."""
    wrappers = []

    for cmd in commands:
        if cmd == "sbatch":
            wrapper = f"""
# lablog auto-logging wrapper for sbatch
{cmd}() {{
    # Log with lablog (will use AI summary if Claude enabled, or script name as fallback)
    lablog log {cmd} "$@"

    # Execute actual command
    command {cmd} "$@"
}}
"""
        elif cmd == "git":
            wrapper = f"""
# lablog auto-logging wrapper for git commit
git() {{
    if [ "$1" = "commit" ]; then
        # Execute git commit
        command git "$@"

        # If commit succeeded, log it with analysis
        if [ $? -eq 0 ]; then
            local commit_msg=$(command git log -1 --pretty=%B)
            # Analyze the commit using lablog
            lablog analyze-diff > /dev/null 2>&1 || true
            lablog note "Git commit: $commit_msg"
        fi
    else
        # Pass through for other git commands
        command git "$@"
    fi
}}
"""
        else:
            wrapper = f"""
# lablog auto-logging wrapper for {cmd}
{cmd}() {{
    lablog log "Executed {cmd}: $*"
    command {cmd} "$@"
}}
"""

        wrappers.append(wrapper)

    header = f"""# lablog shell wrappers
# Generated for {shell}
# Add this to your ~/.{shell}rc or source it separately
"""

    return header + "\n".join(wrappers)


def _detect_shell() -> str:
    """Detect the current shell."""
    import os
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    elif "bash" in shell:
        return "bash"
    else:
        return "bash"  # Default to bash


def _analyze_command_for_scripts(command: tuple, analyzer: ScriptAnalyzer) -> Optional[dict]:
    """Analyze command arguments for script files."""
    for arg in command:
        path = Path(arg)
        if path.exists() and path.is_file():
            # Analyze if it looks like a script
            if path.suffix in [".sh", ".py", ".slurm", ".bash"] or "job" in path.name.lower():
                return analyzer.analyze_script(path)
    return None


def _extract_script_path_from_command(command: tuple) -> Optional[Path]:
    """Extract script path from command arguments."""
    for arg in command:
        path = Path(arg)
        if path.exists() and path.is_file():
            if path.suffix in [".sh", ".py", ".slurm", ".bash"] or "job" in path.name.lower():
                return path
    return None


if __name__ == "__main__":
    cli()
