import json
import os
from pathlib import Path
import time
from typing import Any, Dict
import how.constants as const

class ConfigManager:
    DEFAULT_CONFIG = {
        "model_name": const.MODEL_NAME,
        "ollama_host": const.OLLAMA_HOST,
        "temperature": const.TEMPERATURE,
        "timeout": const.TIMEOUT,
        "log_level": const.LOG_LEVEL,
        "startup_check": const.STARTUP_CHECK
    }

    MAX_HISTORY = 1000
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "how2"
        self.history_dir = self.config_dir / "history"
        self.history_file = self.history_dir / "log.txt"
        self.config_file = self.config_dir / "settings.json"
        self._cache: Dict[str, Any] = {}
        self._load()
        self._ensure_history_exists()

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _ensure_history_exists(self) -> None:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self.history_file.touch()

    def _ensure_exists(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self._write_to_disk(self.DEFAULT_CONFIG)

    def _write_to_disk(self, data: Dict[str, Any]) -> None:
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _load(self) -> None:
        self._ensure_exists()
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  {self.config_file} was corrupted — restoring defaults.")
            data = self.DEFAULT_CONFIG
            self._write_to_disk(data)

        # Merge missing keys
        for k, v in self.DEFAULT_CONFIG.items():
            data.setdefault(k, v)

        self._cache = data
        self._write_to_disk(self._cache)  # persist any new defaults

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        if key == "ollama_host":
            model_name = self._cache.get("model_name", "")
            if model_name.endswith("-cloud"):
                return "https://ollama.com"

        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._write_to_disk(self._cache)

    def load_config(self) -> Dict[str, Any]:
        """Reload configuration from disk."""
        self._load()
        return self._cache

    def save_config(self) -> None:
        """Persist current cache to disk."""
        self._write_to_disk(self._cache)

    def show_config(self) -> None:
        """Pretty print the current config."""
        print(json.dumps(self._cache, indent=4))

    def as_dict(self) -> Dict[str, Any]:
        """Return the current config as a dictionary."""
        return dict(self._cache)


    # --------------------------------------------------
    # Command History
    # --------------------------------------------------
    def log_history(self, question: str, command: str) -> None:
        """Append question and command to log file, keeping max history entries."""
        self._ensure_history_exists()
        command = command.replace('\n', ';')
        entry = f"Q: {question.strip()}\n\t{command.strip()}\n"

        # Read all entries, enforce cap
        with open(self.history_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # If exceeds 1000 entries, drop oldest
        if len(lines) >= self.MAX_HISTORY * 2:  # each entry ~2 lines
            lines = lines[-(self.MAX_HISTORY * 2):]

        lines.append(entry)

        with open(self.history_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def show_history(self, limit: int = 1000) -> None:
        """Pretty print recent command history."""
        self._ensure_history_exists()
        with open(self.history_file, "r", encoding="utf-8") as f:
            entries = f.readlines()

        if not entries:
            print("No history found.")
            return

        # Group entries by question/command pairs
        grouped = []
        buffer = []
        for line in entries:
            buffer.append(line)
            if line.startswith("\t"):
                grouped.append("".join(buffer).strip())
                buffer = []

        if limit:
            grouped = grouped[-limit:]

        for i, entry in enumerate(grouped, start=1):
            print(f"{i}: {entry}\n")

    def get_history_command(self, index: int) -> str | None:
        """Return the command text for a given history index."""
        self._ensure_history_exists()
        with open(self.history_file, "r", encoding="utf-8") as f:
            entries = f.readlines()

        if not entries:
            return None

        grouped = []
        buffer = []
        for line in entries:
            buffer.append(line)
            if line.startswith("\t"):
                grouped.append("".join(buffer).strip())
                buffer = []

        if 1 <= index <= len(grouped):
            entry = grouped[index - 1]
            # Extract command line (the tabbed one)
            for line in entry.splitlines():
                if line.startswith("\t"):
                    return line.strip()
        return None

# Instantiate singleton for global access
config = ConfigManager()
