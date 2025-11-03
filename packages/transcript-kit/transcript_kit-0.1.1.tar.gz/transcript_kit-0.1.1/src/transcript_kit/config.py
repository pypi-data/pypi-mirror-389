"""
Configuration management for transcript-kit

Handles YAML config loading, environment variable substitution,
and platform-aware defaults.

Author: Kevin Callens
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from platformdirs import user_config_dir, user_data_dir


class Config:
    """Configuration manager for transcript-kit"""

    def __init__(self, config_path: Optional[Path] = None, cli_overrides: Optional[Dict] = None):
        """
        Initialize configuration

        Args:
            config_path: Optional path to config file (defaults to platform-appropriate location)
            cli_overrides: Optional dictionary of CLI flag overrides
        """
        self.config_path = config_path or self._get_default_config_path()
        self.cli_overrides = cli_overrides or {}
        self.config = self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get platform-appropriate config file path"""
        config_dir = Path(user_config_dir("transcript-kit"))
        return config_dir / "config.yaml"

    def _get_default_data_dir(self) -> Path:
        """Get platform-appropriate data directory"""
        # On macOS, prefer ~/Documents/transcript-kit for user visibility
        # On Linux/Windows, use platformdirs defaults
        if os.name == "posix" and os.path.exists(Path.home() / "Documents"):
            return Path.home() / "Documents" / "transcript-kit"
        else:
            return Path(user_data_dir("transcript-kit"))

    def _expand_env_vars(self, value: Any) -> Any:
        """
        Recursively expand environment variables in config values

        Supports ${VAR_NAME} syntax
        SECURITY: Never logs expanded values to prevent API key leakage
        """
        if isinstance(value, str):
            # Find all ${VAR_NAME} patterns
            pattern = r'\$\{([^}]+)\}'

            def replace_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))

            return re.sub(pattern, replace_var, value)
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        else:
            return value

    def _get_defaults(self) -> Dict:
        """Get default configuration"""
        return {
            "ai": {
                "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
                "model": os.environ.get("TRANSCRIPT_KIT_AI_MODEL", "openai/gpt-oss-20b"),
                "chunk_size": 8000,
                "context_window": 131000,
                "max_retries": 3,
                "retry_delay": 2,
            },
            "storage": {
                "data_dir": str(self._get_default_data_dir()),
                "raw_subdir": "raw",
                "tags_database": "tags-database.txt",
            },
            "tags": {
                "starter_tags": [],
                "max_tags": 2,
            },
            "processing": {
                "analyze_context": True,
                "auto_tag": True,
            },
        }

    def _load_config(self) -> Dict:
        """
        Load configuration from file, env vars, and defaults

        Precedence (highest to lowest):
        1. CLI overrides
        2. Environment variables (via substitution)
        3. Config file
        4. Defaults
        """
        # Start with defaults
        config = self._get_defaults()

        # Load from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                    # Deep merge file config into defaults
                    config = self._deep_merge(config, file_config)
            except Exception as e:
                # Don't fail if config file is corrupt, just use defaults
                print(f"Warning: Could not load config file: {e}")

        # Expand environment variables
        config = self._expand_env_vars(config)

        # Apply CLI overrides
        if self.cli_overrides:
            config = self._deep_merge(config, self.cli_overrides)

        return config

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation

        Example: config.get('ai.model')
        """
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def save(self, config_dict: Optional[Dict] = None) -> None:
        """
        Save configuration to file

        Args:
            config_dict: Optional config to save (defaults to current config)

        SECURITY: Sets file permissions to 0600 (owner read/write only)
        """
        config_to_save = config_dict or self.config

        # Create config directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write config file
        with open(self.config_path, "w") as f:
            yaml.dump(config_to_save, f, default_flow_style=False, sort_keys=False)

        # Set secure permissions (owner read/write only)
        os.chmod(self.config_path, 0o600)

    def config_exists(self) -> bool:
        """Check if config file exists"""
        return self.config_path.exists()

    def get_data_dir(self) -> Path:
        """Get the data directory as a Path object"""
        data_dir_str = self.get("storage.data_dir")
        # Expand ~ if present
        data_dir = Path(data_dir_str).expanduser()
        return data_dir

    def get_raw_dir(self) -> Path:
        """Get the raw transcripts directory"""
        return self.get_data_dir() / self.get("storage.raw_subdir")

    def get_tags_db_path(self) -> Path:
        """Get the tags database file path"""
        return self.get_data_dir() / self.get("storage.tags_database")

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration

        Returns:
            (is_valid, error_message)
        """
        # Check API key
        api_key = self.get("ai.api_key")
        if not api_key or api_key.startswith("${"):
            return False, "API key not configured. Run 'transcript-kit setup' to configure."

        # Check model
        model = self.get("ai.model")
        if not model:
            return False, "AI model not configured."

        # Check data directory is set
        data_dir = self.get("storage.data_dir")
        if not data_dir:
            return False, "Data directory not configured."

        return True, None

    def display(self, hide_secrets: bool = True) -> str:
        """
        Get a string representation of the config for display

        Args:
            hide_secrets: If True, replaces API keys with ***

        Returns:
            Formatted config string
        """
        display_config = self.config.copy()

        # Hide API key if requested
        if hide_secrets and "ai" in display_config and "api_key" in display_config["ai"]:
            api_key = display_config["ai"]["api_key"]
            if api_key:
                display_config["ai"]["api_key"] = "***" + api_key[-4:] if len(api_key) > 4 else "***"

        return yaml.dump(display_config, default_flow_style=False, sort_keys=False)


def get_config(config_path: Optional[Path] = None, cli_overrides: Optional[Dict] = None) -> Config:
    """
    Factory function to get a Config instance

    Args:
        config_path: Optional path to config file
        cli_overrides: Optional CLI flag overrides

    Returns:
        Config instance
    """
    return Config(config_path=config_path, cli_overrides=cli_overrides)
