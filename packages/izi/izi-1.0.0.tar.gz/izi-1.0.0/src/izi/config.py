"""Configuration management for Gitizi CLI"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manages CLI configuration and token storage"""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory path"""
        if os.name == "nt":  # Windows
            base = Path(os.getenv("APPDATA", "~"))
        else:  # Unix-like (Linux, macOS)
            base = Path(os.getenv("XDG_CONFIG_HOME", "~/.config"))

        return (base / "izi").expanduser()

    def _ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_token(self) -> Optional[str]:
        """Get the stored API token"""
        config = self._load_config()
        return config.get("token")

    def set_token(self, token: str):
        """Store the API token"""
        config = self._load_config()
        config["token"] = token
        self._save_config(config)

    def clear_token(self):
        """Remove the stored API token"""
        config = self._load_config()
        if "token" in config:
            del config["token"]
            self._save_config(config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        config = self._load_config()
        return config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value"""
        config = self._load_config()
        config[key] = value
        self._save_config(config)

    def list_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self._load_config()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_token() is not None


# Global config instance
config = Config()
