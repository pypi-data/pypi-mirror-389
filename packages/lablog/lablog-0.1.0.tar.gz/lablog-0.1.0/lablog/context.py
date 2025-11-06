"""Context detection for lablog entries (git info, environment, etc.)."""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


class ContextDetector:
    """Detects and captures context information for log entries."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize context detector."""
        self.working_dir = working_dir or Path.cwd()

    def get_git_context(self) -> Dict[str, Any]:
        """Get git context (branch, commit, repo status)."""
        context = {}

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["branch"] = result.stdout.strip()

            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["commit"] = result.stdout.strip()

            # Get repo status (clean or dirty)
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["dirty"] = len(result.stdout.strip()) > 0

            # Get remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                context["remote"] = result.stdout.strip()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Git not available or not a git repo
            pass

        return context

    def get_git_root(self) -> Optional[Path]:
        """Get the root of the git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def is_git_repo(self) -> bool:
        """Check if current directory is in a git repository."""
        return self.get_git_root() is not None

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a file and extract useful information."""
        analysis = {
            "path": str(file_path),
            "exists": file_path.exists()
        }

        if not file_path.exists():
            return analysis

        analysis["size_bytes"] = file_path.stat().st_size

        # Try to read the file if it's reasonably sized (< 1MB)
        if analysis["size_bytes"] < 1_000_000:
            try:
                content = file_path.read_text()
                analysis["lines"] = len(content.splitlines())

                # Detect shebang for scripts
                if content.startswith("#!"):
                    analysis["shebang"] = content.splitlines()[0]

                # Count SBATCH directives if it's a SLURM script
                if "#SBATCH" in content:
                    analysis["sbatch_directives"] = content.count("#SBATCH")

            except UnicodeDecodeError:
                analysis["binary"] = True

        return analysis
