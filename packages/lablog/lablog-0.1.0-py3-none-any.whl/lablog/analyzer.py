"""Script analyzer for lablog - extracts key information from job scripts."""

import re
from pathlib import Path
from typing import Dict, Any, List


class ScriptAnalyzer:
    """Analyzes shell scripts, job scripts, and Python files."""

    def analyze_script(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a script file and extract key information."""
        if not file_path.exists():
            return {"error": "File not found"}

        analysis = {
            "path": str(file_path),
            "type": self._detect_type(file_path),
        }

        try:
            content = file_path.read_text()
            analysis["summary"] = self._summarize_content(content, analysis["type"])
        except UnicodeDecodeError:
            analysis["error"] = "Binary file or encoding error"

        return analysis

    def _detect_type(self, file_path: Path) -> str:
        """Detect the type of script."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        if suffix == ".py":
            return "python"
        elif suffix in [".sh", ".bash"]:
            return "shell"
        elif "slurm" in name or "sbatch" in name or suffix == ".slurm":
            return "slurm"
        else:
            return "unknown"

    def _summarize_content(self, content: str, script_type: str) -> Dict[str, Any]:
        """Summarize the content of a script."""
        summary = {}

        if script_type == "slurm":
            summary.update(self._analyze_slurm(content))
        elif script_type == "python":
            summary.update(self._analyze_python(content))
        elif script_type == "shell":
            summary.update(self._analyze_shell(content))

        # Common analysis
        lines = content.splitlines()
        summary["total_lines"] = len(lines)

        # Extract comments at the top (usually describe what the script does)
        summary["description"] = self._extract_description(lines)

        return summary

    def _analyze_slurm(self, content: str) -> Dict[str, Any]:
        """Extract SLURM-specific information."""
        info = {}

        # Extract SBATCH directives
        sbatch_pattern = r"#SBATCH\s+--(\S+)(?:=(\S+))?"
        matches = re.findall(sbatch_pattern, content)

        directives = {}
        for key, value in matches:
            directives[key] = value or True

        if directives:
            info["sbatch_directives"] = directives

        # Look for the main command being executed
        commands = self._extract_main_commands(content)
        if commands:
            info["main_commands"] = commands

        return info

    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Extract Python-specific information."""
        info = {}

        # Count imports
        imports = re.findall(r"^(?:import|from)\s+(\S+)", content, re.MULTILINE)
        if imports:
            info["imports_count"] = len(imports)
            info["key_imports"] = imports[:5]  # First 5 imports

        # Look for argparse or click (indicates CLI script)
        if "argparse" in content or "ArgumentParser" in content:
            info["has_cli"] = "argparse"
        elif "click" in content or "@click.command" in content:
            info["has_cli"] = "click"

        # Look for main function or entry point
        if "if __name__ ==" in content or "def main(" in content:
            info["has_main"] = True

        return info

    def _analyze_shell(self, content: str) -> Dict[str, Any]:
        """Extract shell script information."""
        info = {}

        # Extract shebang
        lines = content.splitlines()
        if lines and lines[0].startswith("#!"):
            info["shebang"] = lines[0]

        # Look for common commands
        commands = self._extract_main_commands(content)
        if commands:
            info["main_commands"] = commands

        return info

    def _extract_main_commands(self, content: str) -> List[str]:
        """Extract main commands from script (heuristic-based)."""
        commands = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Look for common command patterns
            # Python scripts
            if re.match(r"python\s+\S+", line):
                commands.append(line[:80])  # Truncate long lines

            # Common tools
            if any(tool in line for tool in ["sbatch", "srun", "mpirun", "torchrun"]):
                commands.append(line[:80])

        return commands[:3]  # Return first 3 main commands

    def _extract_description(self, lines: List[str]) -> str:
        """Extract description from top comments of the script."""
        description_lines = []

        # Look at first 20 lines for description
        for line in lines[:20]:
            line = line.strip()

            # Stop at first non-comment line (ignoring shebang and sbatch)
            if line and not line.startswith("#"):
                break

            # Skip shebang and sbatch directives
            if line.startswith("#!") or line.startswith("#SBATCH"):
                continue

            # Extract comment text
            if line.startswith("#"):
                comment = line[1:].strip()
                if comment:
                    description_lines.append(comment)

        # Join and truncate
        description = " ".join(description_lines)
        return description[:200] if description else ""
