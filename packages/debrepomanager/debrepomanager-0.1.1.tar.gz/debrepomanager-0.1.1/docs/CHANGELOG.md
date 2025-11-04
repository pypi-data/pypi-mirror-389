# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Retention policy engine with automated cleanup
- Production GitHub Actions workflows for package deployment
- REST API server (optional)
- GPG key rotation feature (v1.1)

## [0.1.1] - 2025-11-03

### Changed
- **Package renamed**: `repomanager` → `debrepomanager`
  - New package name on PyPI: `debrepomanager`
  - Command name: `debrepomanager` (no alias to avoid PyPI conflicts)
  - All imports updated to `debrepomanager`
  - **Migration required**: Replace `repomanager` with `debrepomanager` in scripts
  
### Added
- **PyPI publication workflow**: Automatic publishing on releases
  - Triggered on GitHub release creation
  - Uses `PYPI_TOKEN` secret
  - Package: https://pypi.org/project/debrepomanager/
  
- **GPG Key Rotation plan**: Phase 9 added to roadmap (v1.1)
  - Zero downtime key rotation
  - Grace period support
  - Client migration tools
  - Rollback mechanism
  
- **Deployment Guide**: Complete step-by-step instructions
  - docs/DEPLOYMENT_GUIDE.md
  - Covers /opt/repo + /beta scenario
  - Automated scripts included
  - Client setup examples

### Fixed
- All workflows use self-hosted runners
- Artifacts minimized (0 uploads)
- Integration tests run on all push/PR events

### Documentation
- Git workflow rule added (NEVER push to main!)
- All cursorrules updated for v0.1.1
- 9 comprehensive reports in docs/reports/

## [0.1.0] - 2025-11-03

### Added

#### Core Functionality
- **Configuration management** (`config.py`)
  - YAML-based configuration with merging support
  - Server and repository level configs
  - Comprehensive validation
  - Support for multiple codenames, components, and architectures

- **Aptly wrapper** (`aptly.py`)
  - Multi-root architecture (isolated aptly instances per codename)
  - Repository operations: create, delete, list, verify
  - Atomic package updates via snapshots
  - Automatic snapshot cleanup (configurable retention)
  - Support for multiple architectures (amd64, arm64, riscv64)

- **GPG integration** (`gpg.py`)
  - Automatic GPG signing of all publications
  - Support for gpg-agent with passphrase caching
  - Key availability checking
  - Signing verification

- **Utilities** (`utils.py`)
  - Debian package metadata parsing (python-debian)
  - Version comparison with Debian rules (apt_pkg)
  - Recursive .deb file discovery
  - Package age calculation
  - Structured logging setup

- **CLI interface** (`cli.py`)
  - `add` - Add packages to repository with atomic updates
  - `create-repo` - Create new repository
  - `delete-repo` - Safely delete repository (with confirmation)
  - `list` - List repositories and packages
  - Global options: --config, --verbose, --dry-run
  - Progress indicators and user-friendly error messages

#### Dual Format Support
- **Backward compatibility** for old and new URL formats
  - Old format: `deb http://repo.jethome.ru bookworm component`
  - New format: `deb http://repo.jethome.ru/bookworm component main`
- Automatic symlink creation for old format access
- Configurable via `dual_format.enabled` and `dual_format.auto_symlink`
- Portable relative symlinks for easy repository migration

#### Documentation
- Comprehensive README with examples
- Architecture documentation (ARCHITECTURE.md)
- Implementation plan and progress tracking
- Development guide (DEVELOPMENT.md)
- Configuration reference (CONFIG.md)
- Quick start guide (QUICKSTART.md)
- APT configuration examples (APT_CONFIGURATION.md)
- Dual format technical documentation (DUAL_FORMAT.md)

#### Testing & Quality
- 181 unit tests with 93% code coverage
- Integration test infrastructure (Docker-based)
- pytest configuration with coverage enforcement
- Code quality tools: black, flake8, mypy
- Type hints throughout codebase
- Continuous integration via GitHub Actions

#### CI/CD for Development
- Automatic code review workflow
- Test execution on multiple Python versions (3.11, 3.12)
- Auto-fix workflow for code style issues
- Documentation validation
- Coverage reporting

### Features

- **Multi-distribution support**: bookworm, noble, trixie, jammy
- **Multi-architecture**: amd64, arm64, riscv64
- **Multi-component**: flexible component naming (jethome-tools, jethome-armbian, etc.)
- **Atomic updates**: zero downtime package updates via snapshots
- **Auto-create repositories**: optional automatic repository creation
- **Configurable snapshot retention**: keep last N snapshots per repository
- **Force operations**: recreate existing repositories with --force flag
- **Dry-run mode**: preview operations without making changes

### Technical Details

- Python 3.11+ required
- Dependencies: click, pyyaml, python-debian, apt_pkg (optional)
- Uses aptly for repository management
- Supports GPG signing with configurable key
- Modular architecture with clear separation of concerns

### Configuration

- YAML-based configuration file
- Default locations: `./config.yaml`, `/etc/repomanager/config.yaml`
- Configurable paths for aptly root and publish directories
- Per-component retention policy overrides
- GPG configuration with agent support

[Unreleased]: https://github.com/jethome/repomanager/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/jethome/repomanager/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/jethome/repomanager/releases/tag/v0.1.0

