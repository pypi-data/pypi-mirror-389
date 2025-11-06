"""Claude Code integration for AI-powered analysis."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console

console = Console()


class ClaudeCodeIntegration:
    """Integrates with Claude Code headless mode for AI-powered analysis."""

    def __init__(self):
        """Initialize Claude Code integration."""
        self.claude_available = self._check_claude_available()

    def _check_claude_available(self) -> bool:
        """Check if Claude Code CLI is available."""
        return shutil.which("claude") is not None

    def invoke_claude(
        self,
        prompt: str,
        output_format: str = "text",
        timeout: int = 60,
        allowed_tools: Optional[str] = None
    ) -> Optional[str]:
        """
        Invoke Claude Code headless mode with a prompt.

        Args:
            prompt: The prompt to send to Claude
            output_format: Output format (text, json, stream-json)
            timeout: Timeout in seconds
            allowed_tools: Comma-separated list of allowed tools

        Returns:
            Claude's response or None if failed
        """
        if not self.claude_available:
            console.print("[yellow]⚠ Claude Code CLI not found. Install Claude Code to use AI features.[/yellow]")
            return None

        # Build command
        cmd = ["claude", "-p", prompt, "--output-format", output_format]

        if allowed_tools:
            cmd.extend(["--allowedTools", allowed_tools])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                console.print(f"[red]Claude Code error:[/red] {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            console.print(f"[red]Claude Code timed out after {timeout}s[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error invoking Claude Code:[/red] {e}")
            return None

    def enhance_note(self, note_text: str) -> Optional[str]:
        """
        Enhance a research note while preserving meaning.

        Args:
            note_text: Original note text

        Returns:
            Enhanced note or None if failed
        """
        prompt = f"""Enhance this research note while preserving its meaning:

"{note_text}"

Requirements:
- Fix grammar and spelling
- Make it clear and concise (1-2 sentences max)
- Keep the exact original meaning
- Keep technical terms as-is
- Output ONLY the enhanced note, no explanations"""

        response = self.invoke_claude(prompt, timeout=30)
        return response.strip() if response else None

    def enhance_todo(self, todo_text: str) -> Optional[str]:
        """
        Improve a todo while keeping it actionable.

        Args:
            todo_text: Original todo text

        Returns:
            Enhanced todo or None if failed
        """
        prompt = f"""Improve this research todo while keeping it actionable:

"{todo_text}"

Requirements:
- Fix grammar and structure
- Make it clear and specific
- Keep all technical details
- Ensure it's actionable (starts with verb)
- Output ONLY the improved todo, no explanations"""

        response = self.invoke_claude(prompt, timeout=30)
        return response.strip() if response else None

    def summarize_script(self, script_path: Path) -> Optional[Dict[str, Any]]:
        """
        Use Claude to summarize a script file.

        Args:
            script_path: Path to the script file

        Returns:
            Dictionary with summary information
        """
        if not script_path.exists():
            console.print(f"[red]File not found:[/red] {script_path}")
            return None

        try:
            content = script_path.read_text()
        except UnicodeDecodeError:
            return {"error": "Binary file or encoding error"}

        # Truncate very long scripts
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"

        prompt = f"""Summarize this SLURM job script concisely:

```
{content}
```

Focus ONLY on:
1. What experiment/task is this?
2. Key hyperparameters (lr, model, dataset size, epochs, etc.)
3. Any unique configuration worth noting

IGNORE:
- Resource allocation (memory, GPUs, time limits)
- File paths and module loading
- Boilerplate SBATCH directives

Format as 1-2 sentences max. Be specific about the experiment, not the infrastructure."""

        console.print(f"[cyan]Asking Claude to analyze {script_path.name}...[/cyan]")

        response = self.invoke_claude(prompt, allowed_tools="Read")

        if response:
            return {
                "summary": response,
                "analyzed_by": "claude-code",
                "script_path": str(script_path)
            }

        return None

    def analyze_git_diff(self, working_dir: Path = None) -> Optional[Dict[str, Any]]:
        """
        Use Claude to analyze git changes.

        Args:
            working_dir: Directory to run git diff in

        Returns:
            Dictionary with analysis
        """
        working_dir = working_dir or Path.cwd()

        # Get git diff
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                console.print("[yellow]No git repository or no changes[/yellow]")
                return None

            diff = result.stdout

            if not diff.strip():
                console.print("[yellow]No uncommitted changes[/yellow]")
                return None

        except Exception as e:
            console.print(f"[red]Error getting git diff:[/red] {e}")
            return None

        # Truncate very long diffs
        if len(diff) > 15000:
            diff = diff[:15000] + "\n... (truncated)"

        prompt = f"""Analyze this git diff and summarize what changed:

```diff
{diff}
```

Focus ONLY on:
1. What functionality changed (high-level)
2. Why (if clear from the diff)
3. Important additions or bug fixes

IGNORE:
- Formatting changes
- Import reordering
- Minor refactors unless they change behavior
- Comment-only changes

Be specific and technical. Length: flexible based on amount of changes (1-5 sentences)."""

        console.print("[cyan]Asking Claude to analyze your changes...[/cyan]")

        response = self.invoke_claude(prompt, allowed_tools="Bash,Read")

        if response:
            return {
                "analysis": response,
                "analyzed_by": "claude-code"
            }

        return None

    def enhance_recap(self, entries: list, days: int = 7, job_entries: list = None) -> Optional[str]:
        """
        Use Claude to create an enhanced recap with insights.

        Args:
            entries: List of log entries
            days: Number of days covered
            job_entries: Optional list of job entries

        Returns:
            Enhanced recap text
        """
        if not entries:
            return None

        # Count todos and jobs
        todos = [e for e in entries if e.get("type") == "todo" and e.get("status") != "completed"]
        has_todos = len(todos) > 0
        has_jobs = job_entries and len(job_entries) > 0

        # Format entries for Claude
        entries_text = []
        for entry in entries[-20:]:  # Last 20 entries max
            timestamp = entry.get("timestamp", "")
            entry_type = entry.get("type", "")
            description = entry.get("description", "")
            entries_text.append(f"[{timestamp}] {entry_type}: {description}")

        entries_str = "\n".join(entries_text)

        # Build dynamic prompt sections
        prompt_sections = [
            "1. High-level summary (2-3 sentences) of what I was working on",
            "2. Code changes or experiments summary"
        ]

        if has_todos:
            prompt_sections.append(f"{len(prompt_sections) + 1}. Outstanding todos")
        else:
            prompt_sections.append(f"{len(prompt_sections) + 1}. Note: No current todos")

        sections_str = "\n".join(prompt_sections)

        prompt = f"""I'm a researcher returning to this project. Here are my last {days} days of activity:

{entries_str}

Please provide:
{sections_str}

Keep it concise and actionable. Do NOT ask questions or offer additional help - ONLY provide the summary."""

        console.print("[cyan]Asking Claude to enhance your recap...[/cyan]")

        response = self.invoke_claude(prompt)

        return response

    def merge_entries(self, entries: list, date_from: str, date_to: str) -> Optional[str]:
        """
        Merge multiple entries into one summary.

        Args:
            entries: List of log entries to merge
            date_from: Start date
            date_to: End date

        Returns:
            Merged summary text
        """
        if not entries:
            return None

        # Format entries for Claude
        entries_text = []
        for entry in entries:
            timestamp = entry.get("timestamp", "")
            entry_type = entry.get("type", "")
            description = entry.get("description", "")
            entries_text.append(f"[{timestamp}] {entry_type}: {description}")

        entries_str = "\n".join(entries_text)

        prompt = f"""Merge these research log entries from {date_from} to {date_to} into a concise summary.

Entries:
{entries_str}

Group by themes/topics if possible. Format as a clear summary (3-5 sentences) that captures:
1. Main activities during this period
2. Key findings or results
3. Important technical details

Be concise but preserve critical information. Do NOT ask questions."""

        console.print(f"[cyan]Merging {len(entries)} entries with Claude...[/cyan]")

        response = self.invoke_claude(prompt, timeout=90)

        return response

    def analyze_job_output(self, output_file: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a job output file for success/failure.

        Args:
            output_file: Path to job output file

        Returns:
            Dictionary with analysis
        """
        if not output_file.exists():
            return {"status": "not_found", "message": "Output file not found"}

        try:
            # Read last 1000 lines for analysis (avoid huge files)
            with open(output_file, 'r') as f:
                lines = f.readlines()
                content = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
        except Exception as e:
            return {"status": "error", "message": f"Could not read file: {e}"}

        # Truncate if still too long
        if len(content) > 15000:
            content = content[-15000:]

        prompt = f"""Analyze this job output file for success/failure:

```
{content}
```

Report concisely (2-3 sentences):
1. Did it complete successfully?
2. Any errors or warnings?
3. Key results if available

Be specific and actionable. Do NOT ask questions."""

        console.print(f"[cyan]Analyzing {output_file.name}...[/cyan]")

        response = self.invoke_claude(prompt, timeout=60, allowed_tools="Read")

        if response:
            return {
                "status": "analyzed",
                "analysis": response,
                "file": str(output_file)
            }

        return None
