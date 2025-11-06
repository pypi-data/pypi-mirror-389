"""Storage layer for lablog entries using JSONL format."""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


class LablogStorage:
    """Manages reading/writing lablog entries to JSONL files."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize storage with config directory."""
        if config_dir is None:
            config_dir = Path.home() / ".config" / "lablog"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Global log for cross-project entries
        self.global_log = self.config_dir / "global.jsonl"

        # Project-specific logs
        self.projects_dir = self.config_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)

    def get_project_id(self, project_root: Path) -> str:
        """Generate a unique ID for a project based on its path."""
        return hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]

    def get_project_dir(self, project_root: Path) -> Path:
        """Get the project directory."""
        project_id = self.get_project_id(project_root)
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(exist_ok=True)

        # Store project metadata
        metadata_file = project_dir / "metadata.json"
        if not metadata_file.exists():
            metadata = {
                "project_root": str(project_root.resolve()),
                "created_at": datetime.now().isoformat()
            }
            metadata_file.write_text(json.dumps(metadata, indent=2))

        return project_dir

    def get_project_log(self, project_root: Path) -> Path:
        """Get the log file for a specific project (regular entries, not jobs)."""
        return self.get_project_dir(project_root) / "log.jsonl"

    def get_project_jobs_log(self, project_root: Path) -> Path:
        """Get the jobs log file for a specific project."""
        return self.get_project_dir(project_root) / "jobs.jsonl"

    def get_project_archive_log(self, project_root: Path) -> Path:
        """Get the archive log file for a specific project."""
        return self.get_project_dir(project_root) / "archive.jsonl"

    def append_entry(self, entry: Dict[str, Any], project_root: Optional[Path] = None):
        """Append an entry to the appropriate log file."""
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()

        # Determine which log file to use
        if project_root:
            log_file = self.get_project_log(project_root)
        else:
            log_file = self.global_log

        # Append to JSONL
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def read_entries(
        self,
        project_root: Optional[Path] = None,
        days: Optional[int] = None,
        entry_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Read entries from log file with optional filtering."""
        # Determine which log file to read
        if project_root:
            log_file = self.get_project_log(project_root)
        else:
            log_file = self.global_log

        if not log_file.exists():
            return []

        entries = []
        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)

                    # Filter by date
                    if cutoff_date:
                        entry_date = datetime.fromisoformat(entry["timestamp"])
                        if entry_date < cutoff_date:
                            continue

                    # Filter by type
                    if entry_type and entry.get("type") != entry_type:
                        continue

                    entries.append(entry)

        return entries

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get metadata for all tracked projects."""
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    metadata["project_id"] = project_dir.name
                    projects.append(metadata)
        return projects

    def append_job_entry(self, entry: Dict[str, Any], project_root: Optional[Path] = None):
        """Append a job entry to the jobs log file."""
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()

        # Ensure type is 'job'
        entry["type"] = "job"

        # Determine which log file to use
        if project_root:
            log_file = self.get_project_jobs_log(project_root)
        else:
            log_file = self.global_log  # Fallback

        # Append to JSONL
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def read_job_entries(
        self,
        project_root: Optional[Path] = None,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Read job entries from jobs log file."""
        # Determine which log file to read
        if project_root:
            log_file = self.get_project_jobs_log(project_root)
        else:
            return []

        if not log_file.exists():
            return []

        entries = []
        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)

                    # Filter by date
                    if cutoff_date:
                        entry_date = datetime.fromisoformat(entry["timestamp"])
                        if entry_date < cutoff_date:
                            continue

                    entries.append(entry)

        return entries

    def archive_entries(
        self,
        entries: List[Dict[str, Any]],
        project_root: Optional[Path] = None,
        reason: str = "manual"
    ):
        """Move entries to archive."""
        if not entries:
            return

        # Separate jobs from regular entries
        job_entries = [e for e in entries if e.get("type") == "job"]
        regular_entries = [e for e in entries if e.get("type") != "job"]

        # Get archive file
        if project_root:
            archive_file = self.get_project_archive_log(project_root)
        else:
            archive_file = self.config_dir / "archive.jsonl"

        # Add archive metadata and write to archive
        for entry in entries:
            entry["archived_at"] = datetime.now().isoformat()
            entry["archive_reason"] = reason

            # Append to archive
            with open(archive_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Remove from original log files
        if regular_entries:
            self._remove_entries_from_log(regular_entries, project_root)
        if job_entries:
            self._remove_entries_from_jobs_log(job_entries, project_root)

    def _remove_entries_from_log(
        self,
        entries_to_remove: List[Dict[str, Any]],
        project_root: Optional[Path] = None
    ):
        """Remove specific entries from log file."""
        # Determine which log file
        if project_root:
            log_file = self.get_project_log(project_root)
        else:
            log_file = self.global_log

        if not log_file.exists():
            return

        # Read all entries
        all_entries = []
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    all_entries.append(json.loads(line))

        # Create set of timestamps to remove
        timestamps_to_remove = {e["timestamp"] for e in entries_to_remove}

        # Write back only entries not in removal set
        with open(log_file, "w") as f:
            for entry in all_entries:
                if entry["timestamp"] not in timestamps_to_remove:
                    f.write(json.dumps(entry) + "\n")

    def _remove_entries_from_jobs_log(
        self,
        entries_to_remove: List[Dict[str, Any]],
        project_root: Optional[Path] = None
    ):
        """Remove specific job entries from jobs log file."""
        # Determine which jobs log file
        if project_root:
            jobs_file = self.get_project_jobs_log(project_root)
        else:
            return  # No global jobs log

        if not jobs_file.exists():
            return

        # Read all job entries
        all_jobs = []
        with open(jobs_file, "r") as f:
            for line in f:
                if line.strip():
                    all_jobs.append(json.loads(line))

        # Create set of timestamps to remove
        timestamps_to_remove = {e["timestamp"] for e in entries_to_remove}

        # Write back only jobs not in removal set
        with open(jobs_file, "w") as f:
            for job in all_jobs:
                if job["timestamp"] not in timestamps_to_remove:
                    f.write(json.dumps(job) + "\n")

    def read_archive_entries(
        self,
        project_root: Optional[Path] = None,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Read archived entries."""
        if project_root:
            archive_file = self.get_project_archive_log(project_root)
        else:
            archive_file = self.config_dir / "archive.jsonl"

        if not archive_file.exists():
            return []

        entries = []
        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        with open(archive_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)

                    # Filter by original timestamp, not archived_at
                    if cutoff_date and "timestamp" in entry:
                        entry_date = datetime.fromisoformat(entry["timestamp"])
                        if entry_date < cutoff_date:
                            continue

                    entries.append(entry)

        return entries

    def delete_archive_entries(
        self,
        entries_to_delete: List[Dict[str, Any]],
        project_root: Optional[Path] = None
    ):
        """Permanently delete entries from archive."""
        if not entries_to_delete:
            return

        if project_root:
            archive_file = self.get_project_archive_log(project_root)
        else:
            archive_file = self.config_dir / "archive.jsonl"

        if not archive_file.exists():
            return

        # Read all archived entries
        all_entries = []
        with open(archive_file, "r") as f:
            for line in f:
                if line.strip():
                    all_entries.append(json.loads(line))

        # Create set of timestamps to delete
        timestamps_to_delete = {e["timestamp"] for e in entries_to_delete}

        # Write back only entries not in deletion set
        with open(archive_file, "w") as f:
            for entry in all_entries:
                if entry["timestamp"] not in timestamps_to_delete:
                    f.write(json.dumps(entry) + "\n")

    def update_entry(
        self,
        timestamp: str,
        updates: Dict[str, Any],
        project_root: Optional[Path] = None,
        is_job: bool = False
    ):
        """Update a specific entry by timestamp."""
        # Determine which log file
        if project_root:
            log_file = self.get_project_jobs_log(project_root) if is_job else self.get_project_log(project_root)
        else:
            log_file = self.global_log

        if not log_file.exists():
            return

        # Read all entries
        all_entries = []
        updated = False
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry["timestamp"] == timestamp:
                        entry.update(updates)
                        updated = True
                    all_entries.append(entry)

        # Write back if updated
        if updated:
            with open(log_file, "w") as f:
                for entry in all_entries:
                    f.write(json.dumps(entry) + "\n")
