# Debian Repository Manager (debrepomanager)

A system for managing multiple Debian-like repositories with support for multiple distributions, architectures, and package collections, featuring atomic updates and GitHub Actions integration.

[![Tests](https://github.com/jethome-iot/repomanager/workflows/Tests/badge.svg)](https://github.com/jethome-iot/repomanager/actions)
[![PyPI version](https://badge.fury.io/py/debrepomanager.svg)](https://pypi.org/project/debrepomanager/)
[![Python](https://img.shields.io/pypi/pyversions/debrepomanager.svg)](https://pypi.org/project/debrepomanager/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](https://github.com/jethome-iot/repomanager)

## Features

- 🚀 **Atomic updates** via aptly snapshots
- 🔄 **Multi-codename**: bookworm, noble, trixie, jammy, etc.
- 🏗️ **Multi-architecture**: amd64, arm64, riscv64
- 📦 **Multi-component**: various package collections
- 🔐 **GPG signing** for all repositories
- 🧹 **Retention policies**: automatic cleanup of old versions
- 🤖 **GitHub Actions**: CI/CD pipeline integration
- 🔍 **Verification**: repository consistency checks
- 🔀 **Dual format**: old and new APT URL formats support

## Architecture

Built on top of [aptly](https://www.aptly.info/) with:
- Multi-root isolation (separate aptly root per codename)
- Snapshots for atomic operations
- Python CLI for easy management
- GitHub Actions for automation

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed description.

## Requirements

### Server
- aptly >= 1.5.0
- gpg (GnuPG) >= 2.2
- Python >= 3.11
- rsync (for GitHub Actions)
- SSH server (for GitHub Actions)

### Development
- Python >= 3.11 (tested on 3.11, 3.12, 3.13)
- pip
- virtualenv (recommended)
- Docker (for integration tests)

## Installation

### From PyPI

```bash
pip install debrepomanager
```

### From source

```bash
git clone https://github.com/jethome-iot/repomanager.git
cd repomanager
pip install -e .
```

### For development

```bash
git clone https://github.com/jethome-iot/repomanager.git
cd repomanager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Quick Start

```bash
# Create repository
debrepomanager create-repo --codename bookworm --component jethome-tools

# Add packages
debrepomanager add --codename bookworm --component jethome-tools --package-dir /path/to/packages/

# List repositories
debrepomanager list

# List packages in repository
debrepomanager list --codename bookworm --component jethome-tools
```

## Configuration

Main configuration file: `config.yaml`

```yaml
gpg:
  key_id: "1234567890ABCDEF"
  use_agent: true

aptly:
  root_base: "/srv/aptly"
  publish_base: "/srv/repo/public"

retention:
  default:
    min_versions: 5
    max_age_days: 90

repositories:
  codenames:
    - bookworm
    - noble
    - trixie
    - jammy
  components:
    - jethome-tools
    - jethome-armbian
  architectures:
    - amd64
    - arm64
    - riscv64
  auto_create: true
  dual_format:
    enabled: true
    method: symlink
    auto_symlink: true
```

See `config.yaml.example` for all available options.

## Usage

### Create repository

```bash
debrepomanager create-repo --codename bookworm --component jethome-tools
```

### Add packages

```bash
# Add specific packages
debrepomanager add --codename bookworm --component jethome-tools \
    --packages package1.deb package2.deb

# Add all packages from directory
debrepomanager add --codename bookworm --component jethome-tools \
    --package-dir /path/to/packages/
```

### List repositories and packages

```bash
# List all repositories
debrepomanager list

# List repositories for specific codename
debrepomanager list --codename bookworm

# List packages in repository
debrepomanager list --codename bookworm --component jethome-tools
```

### Delete repository

```bash
debrepomanager delete-repo --codename bookworm --component old-component --confirm
```

## Client Configuration

### Debian Bookworm

```bash
# Import GPG key
wget -qO - http://repo.site.com/pubkey.gpg | \
    sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/jethome.gpg

# Add repository (new format)
echo "deb http://repo.site.com/bookworm jethome-tools main" | \
    sudo tee /etc/apt/sources.list.d/jethome.list

# Update
sudo apt update

# Install packages
sudo apt install your-package
```

### Ubuntu Noble

```bash
# Import GPG key
wget -qO - http://repo.site.com/pubkey.gpg | \
    sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/jethome.gpg

# Add repository
echo "deb http://repo.site.com/noble jethome-tools main" | \
    sudo tee /etc/apt/sources.list.d/jethome.list

# Update
sudo apt update
```

## Dual Format Support

The system supports both old and new APT URL formats simultaneously:

**Old format** (backward compatibility):
```
deb http://repo.site.com bookworm jethome-tools
```

**New format** (recommended):
```
deb http://repo.site.com/bookworm jethome-tools main
```

Both formats work simultaneously via symlinks. See [DUAL_FORMAT.md](docs/DUAL_FORMAT.md) for technical details.

## Repository URL Structure

Repositories are accessible via:
```
http://repo.site.com/{codename}/{component}
```

Examples:
```
http://repo.site.com/bookworm/jethome-tools
http://repo.site.com/noble/jethome-armbian
http://repo.site.com/trixie/jethome-bookworm
```

## Development

### Project Structure

```
debrepomanager/
├── debrepomanager/        # Main package
│   ├── __init__.py
│   ├── cli.py            # CLI interface
│   ├── aptly.py          # Aptly wrapper
│   ├── config.py         # Configuration management
│   ├── gpg.py            # GPG operations
│   └── utils.py          # Utilities
├── tests/                # Tests
├── docs/                 # Documentation
├── .github/workflows/    # GitHub Actions
└── config.yaml.example   # Configuration example
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=debrepomanager --cov-report=html

# Specific module
pytest tests/test_config.py

# Verbose
pytest -v
```

### Code Quality

Project uses:
- **Black** for formatting (spaces, not tabs)
- **flake8** for linting
- **mypy** for type checking

```bash
# Format
black debrepomanager/

# Lint
flake8 debrepomanager/

# Type check
mypy debrepomanager/
```

## Documentation

### For Users
- [Quick Start](docs/QUICKSTART.md) - 5-minute getting started guide
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [APT Configuration](docs/APT_CONFIGURATION.md) - Client setup for all systems

### For Administrators
- [Configuration Reference](docs/CONFIG.md) - Detailed config options

### For Developers
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [Architecture](docs/ARCHITECTURE.md) - Architecture decisions
- [Development Guide](docs/DEVELOPMENT.md) - Developer workflow
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Code organization

## Troubleshooting

### GPG signing fails

```bash
# Check key availability
gpg --list-secret-keys

# Check gpg-agent
gpg-connect-agent 'keyinfo --list' /bye

# Restart gpg-agent
gpgconf --kill gpg-agent
gpg-connect-agent /bye
```

### Aptly errors

```bash
# Check repository status
debrepomanager list

# Check snapshots (via aptly directly)
aptly -config /srv/aptly/bookworm/aptly.conf snapshot list

# Check published repositories
aptly -config /srv/aptly/bookworm/aptly.conf publish list
```

### Permission issues

```bash
# Check permissions
ls -la /srv/aptly/
ls -la /srv/repo/public/

# Fix permissions
chown -R repomanager:repomanager /srv/aptly/
chown -R www-data:repomanager /srv/repo/public/
chmod -R g+w /srv/aptly/ /srv/repo/public/
```

## GitHub Actions Integration

For CI/CD workflows, configure GitHub Secrets:

- `SSH_PRIVATE_KEY`: SSH key for server access
- `SSH_HOST`: Server address (e.g., repo.site.com)
- `SSH_USER`: SSH user (e.g., repomanager)
- `GPG_PRIVATE_KEY`: GPG private key (base64 encoded)
- `GPG_PASSPHRASE`: GPG key password
- `GPG_KEY_ID`: GPG key ID

See [WORKFLOWS.md](docs/WORKFLOWS.md) for detailed GitHub Actions documentation.

## License

MIT License - see [LICENSE](LICENSE)

## Authors

JetHome Team

## Contributing

Pull requests are welcome! Please make sure to:
1. Add tests for new functionality
2. Update documentation
3. Follow code style (black, flake8)
4. Ensure all tests pass

## Links

- **Documentation**: [docs/](docs/)
- **PyPI**: https://pypi.org/project/debrepomanager/
- **Issues**: https://github.com/jethome-iot/repomanager/issues
- **Discussions**: https://github.com/jethome-iot/repomanager/discussions

## Project Status

- **Version**: 0.1.2
- **Status**: Production Ready (95% MVP)
- **Tests**: 194 tests, 93% coverage
- **Python**: 3.11, 3.12, 3.13 supported

---

**Made with ❤️ by JetHome Team**
