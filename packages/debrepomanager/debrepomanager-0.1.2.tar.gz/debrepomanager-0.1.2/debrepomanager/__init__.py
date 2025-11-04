"""
Debian Repository Manager (debrepomanager)

A system for managing Debian-like repositories with support for multiple
distributions, architectures, and components.
"""

__version__ = "0.1.2"
__author__ = "JetHome Team"
__email__ = "support@jethome.ru"

# Phase 1: Aptly Base ✅
from debrepomanager.aptly import AptlyError, AptlyManager

# Note: Imports added as modules are implemented
# Phase 1: Config ✅
from debrepomanager.config import Config, ConfigError

# Phase 4: GPG ✅
from debrepomanager.gpg import GPGError, GPGManager

# Phase 1: Utils ✅
from debrepomanager.utils import (
    PackageInfo,
    compare_versions,
    find_deb_files,
    get_package_age,
    parse_deb_metadata,
    setup_logging,
)

# Phase 8: Retention (not in MVP)
# from debrepomanager.retention import RetentionPolicy

__all__ = [
    "Config",
    "ConfigError",
    "AptlyManager",
    "AptlyError",
    "GPGManager",
    "GPGError",
    "PackageInfo",
    "setup_logging",
    "parse_deb_metadata",
    "compare_versions",
    "find_deb_files",
    "get_package_age",
    "__version__",
]
