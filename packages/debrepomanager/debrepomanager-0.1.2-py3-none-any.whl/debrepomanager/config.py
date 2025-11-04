"""Configuration management for Debian Repository Manager.

This module handles loading and merging configuration from YAML files,
with support for repository and server-level configs.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration related errors."""


class Config:
    """Configuration manager for debrepomanager.

    Loads configuration from YAML files with support for:
    - Default configuration
    - Repository-level config (./config.yaml)
    - Server-level config (/etc/repomanager/config.yaml)
    - Configuration merging (server overrides repository)

    Attributes:
        _config: Internal configuration dictionary

    Example:
        >>> config = Config()
        >>> config.load("config.yaml")
        >>> aptly_root = config.get_aptly_root("bookworm")
    """

    DEFAULT_CONFIG: Dict[str, Any] = {
        "aptly": {
            "root_base": "/srv/aptly",
            "publish_base": "/srv/repo/public",
            "aptly_path": "aptly",
        },
        "gpg": {
            "key_id": "",
            "use_agent": True,
            "gpg_path": "gpg",
        },
        "retention": {
            "default": {
                "min_versions": 5,
                "max_age_days": 90,
            },
            "overrides": {},
        },
        "repositories": {
            "codenames": ["bookworm", "noble", "trixie", "jammy"],
            "components": ["jethome-tools", "jethome-armbian"],
            "architectures": ["amd64", "arm64", "riscv64"],
            "auto_create": True,
            "dual_format": {
                "enabled": True,
                "method": "symlink",
                "auto_symlink": True,
            },
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "advanced": {
            "max_snapshots": 10,
            "snapshot_format": "{component}-{codename}-%Y%m%d-%H%M%S%f",
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Optional path to config file. If not provided,
                        will try to load from default locations.
        """
        self._config: Dict[str, Any] = {}
        self.load_default()

        if config_path:
            self.load(config_path)

        # Try to load server config (overrides repository config)
        server_config_path = Path("/etc/repomanager/config.yaml")
        if server_config_path.exists():
            try:
                self.load(str(server_config_path), merge=True)
                logger.debug(f"Loaded server config from {server_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load server config: {e}")

    def load_default(self) -> None:
        """Load default configuration."""
        self._config = self._deep_copy_dict(self.DEFAULT_CONFIG)
        logger.debug("Loaded default configuration")

    def load(self, config_path: str, merge: bool = False) -> None:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file
            merge: If True, merge with existing config. If False, replace.

        Raises:
            ConfigError: If file not found or invalid YAML
        """
        path = Path(config_path)

        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            with path.open("r") as f:
                loaded_config = yaml.safe_load(f)

            if loaded_config is None:
                loaded_config = {}

            if merge:
                self._merge_dict(self._config, loaded_config)
                logger.debug(f"Merged configuration from {config_path}")
            else:
                self._config = loaded_config
                logger.debug(f"Loaded configuration from {config_path}")

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}")
        except PermissionError:
            raise ConfigError(f"Permission denied reading {config_path}")

    def _deep_copy_dict(self, d: Dict) -> Dict:
        """Deep copy a dictionary."""
        import copy

        return copy.deepcopy(d)

    def _merge_dict(self, base: Dict, override: Dict) -> None:
        """Recursively merge override dict into base dict.

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    # Property accessors for main config sections

    @property
    def aptly_root_base(self) -> str:
        """Get aptly root base directory."""
        return str(self._config["aptly"]["root_base"])

    @property
    def publish_base(self) -> str:
        """Get publish base directory."""
        return str(self._config["aptly"]["publish_base"])

    @property
    def aptly_path(self) -> str:
        """Get path to aptly binary."""
        return str(self._config["aptly"].get("aptly_path", "aptly"))

    @property
    def gpg_key_id(self) -> str:
        """Get GPG key ID."""
        key_id = self._config["gpg"]["key_id"]
        if not key_id:
            raise ConfigError("GPG key_id not configured")
        return str(key_id)

    @property
    def gpg_use_agent(self) -> bool:
        """Check if gpg-agent should be used."""
        return bool(self._config["gpg"].get("use_agent", True))

    @property
    def gpg_path(self) -> str:
        """Get path to gpg binary."""
        return str(self._config["gpg"].get("gpg_path", "gpg"))

    def get_aptly_root(self, codename: str) -> str:
        """Get aptly root directory for specific codename.

        Args:
            codename: Distribution codename (e.g., 'bookworm')

        Returns:
            Path to aptly root for this codename
        """
        return str(Path(self.aptly_root_base) / codename)

    def get_codenames(self) -> List[str]:
        """Get list of supported codenames.

        Returns:
            List of distribution codenames
        """
        return list(self._config["repositories"]["codenames"])

    def get_components(self) -> List[str]:
        """Get list of repository components.

        Returns:
            List of component names
        """
        return list(self._config["repositories"]["components"])

    def get_architectures(self) -> List[str]:
        """Get list of supported architectures.

        Returns:
            List of architectures (e.g., ['amd64', 'arm64', 'riscv64'])
        """
        return list(self._config["repositories"]["architectures"])

    @property
    def auto_create_repos(self) -> bool:
        """Check if repositories should be auto-created.

        Returns:
            True if auto-create is enabled
        """
        return bool(self._config["repositories"].get("auto_create", True))

    @property
    def dual_format_enabled(self) -> bool:
        """Check if dual format support is enabled.

        Returns:
            True if dual format (old + new URL) is enabled
        """
        dual_format = self._config["repositories"].get("dual_format", {})
        return bool(dual_format.get("enabled", True))

    @property
    def dual_format_method(self) -> str:
        """Get dual format implementation method.

        Returns:
            Method name: 'symlink', 'nginx', or 'dual_publish'
        """
        dual_format = self._config["repositories"].get("dual_format", {})
        return str(dual_format.get("method", "symlink"))

    @property
    def dual_format_auto_symlink(self) -> bool:
        """Check if symlinks should be created automatically.

        Returns:
            True if auto-symlink is enabled
        """
        dual_format = self._config["repositories"].get("dual_format", {})
        return bool(dual_format.get("auto_symlink", True))

    @property
    def logging_level(self) -> str:
        """Get logging level.

        Returns:
            Logging level string (DEBUG, INFO, WARNING, ERROR)
        """
        return str(self._config["logging"].get("level", "INFO"))

    @property
    def logging_format(self) -> str:
        """Get logging format string.

        Returns:
            Python logging format string
        """
        return str(
            self._config["logging"].get(
                "format", "%(asctime)s - %(levelname)s - %(message)s"
            )
        )

    @property
    def max_snapshots(self) -> int:
        """Get maximum number of snapshots to keep.

        Returns:
            Maximum snapshots count
        """
        return int(self._config["advanced"].get("max_snapshots", 10))

    @property
    def snapshot_format(self) -> str:
        """Get snapshot naming format.

        Returns:
            Snapshot format string with placeholders
        """
        return str(
            self._config["advanced"].get(
                "snapshot_format", "{component}-{codename}-%Y%m%d-%H%M%S"
            )
        )

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ConfigError: If configuration is invalid
        """
        # Check required sections
        required_sections = ["aptly", "gpg", "repositories"]
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"Missing required section: {section}")

        # Validate aptly paths
        aptly_root = Path(self.aptly_root_base)
        if not aptly_root.is_absolute():
            raise ConfigError(f"aptly.root_base must be absolute path: {aptly_root}")

        publish_base = Path(self.publish_base)
        if not publish_base.is_absolute():
            raise ConfigError(
                f"aptly.publish_base must be absolute path: {publish_base}"
            )

        # Validate GPG key_id is set
        if not self._config["gpg"]["key_id"]:
            logger.warning("GPG key_id not configured - signing will fail")

        # Validate codenames, components, architectures are lists
        repos = self._config["repositories"]
        if not isinstance(repos.get("codenames"), list):
            raise ConfigError("repositories.codenames must be a list")
        if not isinstance(repos.get("components"), list):
            raise ConfigError("repositories.components must be a list")
        if not isinstance(repos.get("architectures"), list):
            raise ConfigError("repositories.architectures must be a list")

        logger.debug("Configuration validation passed")
