"""Configuration management for lablog."""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class LablogConfig:
    """Manages lablog configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager."""
        if config_dir is None:
            config_dir = Path.home() / ".config" / "lablog"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        # Load existing config or create default
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config from file or return defaults."""
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except json.JSONDecodeError:
                # Corrupted config, return defaults
                pass

        # Default configuration
        return {
            "claude_enabled": False,
            "hooks_enabled": False,
            "auto_enhance_notes": False,
            "auto_enhance_todos": False,
        }

    def save(self):
        """Save configuration to file."""
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def is_claude_enabled(self) -> bool:
        """Check if Claude Code integration is enabled."""
        return self.config.get("claude_enabled", False)

    def enable_claude(self):
        """Enable Claude Code integration."""
        self.config["claude_enabled"] = True
        self.save()

    def disable_claude(self):
        """Disable Claude Code integration."""
        self.config["claude_enabled"] = False
        self.save()

    def is_hooks_enabled(self) -> bool:
        """Check if shell hooks are enabled."""
        return self.config.get("hooks_enabled", False)

    def enable_hooks(self):
        """Enable shell hooks."""
        self.config["hooks_enabled"] = True
        self.save()

    def disable_hooks(self):
        """Disable shell hooks."""
        self.config["hooks_enabled"] = False
        self.save()

    def should_auto_enhance_notes(self) -> bool:
        """Check if notes should be auto-enhanced."""
        return self.config.get("auto_enhance_notes", False)

    def should_auto_enhance_todos(self) -> bool:
        """Check if todos should be auto-enhanced."""
        return self.config.get("auto_enhance_todos", False)

    def set_auto_enhance_notes(self, enabled: bool):
        """Set auto-enhance for notes."""
        self.config["auto_enhance_notes"] = enabled
        self.save()

    def set_auto_enhance_todos(self, enabled: bool):
        """Set auto-enhance for todos."""
        self.config["auto_enhance_todos"] = enabled
        self.save()
