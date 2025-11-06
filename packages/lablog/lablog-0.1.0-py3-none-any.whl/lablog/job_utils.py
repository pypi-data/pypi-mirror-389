"""Utilities for handling job entries and checking status."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


def extract_output_file_from_script(script_path: Path) -> Optional[str]:
    """
    Extract output file path from SBATCH script.

    Args:
        script_path: Path to the script file

    Returns:
        Output file path if found, None otherwise
    """
    if not script_path.exists():
        return None

    try:
        content = script_path.read_text()
    except Exception:
        return None

    # Look for #SBATCH --output=<path> or #SBATCH -o <path>
    patterns = [
        r'#SBATCH\s+--output[=\s]+(\S+)',
        r'#SBATCH\s+-o\s+(\S+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)

    return None


def check_job_status(job_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check the status of a job entry.

    Args:
        job_entry: Job entry from jobs.jsonl

    Returns:
        Status dictionary with:
        - status: 'success', 'not_found', 'old_file', 'error'
        - message: Human-readable status message
        - output_file: Path to output file if available
        - needs_analysis: Whether Claude should analyze the output
    """
    output_file_path = job_entry.get("output_file")
    timestamp = job_entry.get("timestamp")

    if not output_file_path:
        return {
            "status": "no_output",
            "message": "No output file path found in entry",
            "needs_analysis": False
        }

    output_file = Path(output_file_path)

    if not output_file.exists():
        return {
            "status": "not_found",
            "message": "Output file not created yet (job may be queued/running)",
            "output_file": str(output_file),
            "needs_analysis": False
        }

    # Check if file is newer than entry
    try:
        file_mtime = output_file.stat().st_mtime
        entry_time = datetime.fromisoformat(timestamp).timestamp()

        if file_mtime < entry_time:
            return {
                "status": "old_file",
                "message": "Output file older than log entry (stale)",
                "output_file": str(output_file),
                "needs_analysis": False
            }

        # File exists and is recent - needs analysis
        return {
            "status": "found",
            "message": "Output file exists (recent)",
            "output_file": str(output_file),
            "needs_analysis": True
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking file: {e}",
            "output_file": str(output_file),
            "needs_analysis": False
        }


def summarize_job_statuses(job_statuses: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Summarize job statuses for display.

    Args:
        job_statuses: List of job status dictionaries

    Returns:
        Summary counts by status
    """
    summary = {
        "found": 0,
        "not_found": 0,
        "old_file": 0,
        "no_output": 0,
        "error": 0
    }

    for status in job_statuses:
        status_key = status.get("status", "error")
        if status_key in summary:
            summary[status_key] += 1

    return summary
