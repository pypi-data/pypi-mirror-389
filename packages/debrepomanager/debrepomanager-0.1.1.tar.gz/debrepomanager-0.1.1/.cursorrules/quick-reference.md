# Quick Reference

## 📚 Documentation Locations

### Main Documentation
- **README.md** (root) - Main project page, CLI commands, examples
- **docs/README.md** - Documentation index and navigation
- **docs/START_HERE.md** - Entry point для новых пользователей

### For Users
- **docs/QUICKSTART.md** - Быстрый старт за 5 минут
- **docs/APT_CONFIGURATION.md** - Настройка APT клиентов
- **docs/CONFIG.md** - Configuration reference
- **docs/DUAL_FORMAT.md** - Dual format URL support

### For Developers
- **docs/DEVELOPMENT.md** - Developer workflow guide
- **docs/ARCHITECTURE.md** - Architecture and design decisions
- **docs/IMPLEMENTATION_STEPS.md** - Code examples for each module
- **docs/TODO.md** - Task checklist (updated for v0.1.0)
- **docs/PROJECT_STRUCTURE.md** - Project structure overview

### For DevOps
- **docs/WORKFLOWS.md** - GitHub Actions workflows
- **config.yaml.example** (root) - Configuration template

### Planning & Status
- **docs/IMPLEMENTATION_PLAN.md** - Implementation plan (95% complete)
- **docs/PHASES_OVERVIEW.md** - Phases overview
- **docs/CHANGELOG.md** - Change history (v0.1.0)
- **docs/reports/PROJECT_STATUS.md** - Current project status
- **docs/reports/ИТОГОВЫЙ_АНАЛИЗ.md** - Comprehensive analysis

## 🔧 Make Commands

```bash
make help              # Show all commands

# Development
make install           # Install package
make install-dev       # Install with dev dependencies

# Testing
make test              # Run tests
make test-verbose      # Verbose test output
make test-coverage     # Tests with coverage report

# Code Quality
make format            # Format code (Black)
make format-check      # Check formatting without changes
make lint              # Lint code (flake8)
make type-check        # Type check (mypy)

# All Checks
make check-all         # Run all checks (before commit!)

# Cleanup
make clean             # Remove build artifacts
```

## 🐍 Python Commands

```bash
# Format
black repomanager/ tests/

# Lint
flake8 repomanager/ tests/

# Type check
mypy repomanager/

# Test
pytest
pytest -v              # Verbose
pytest -vv             # Extra verbose
pytest -s              # Show prints
pytest --cov           # With coverage

# Test specific
pytest tests/test_config.py
pytest tests/test_config.py::test_function
pytest -m unit         # Only unit tests
pytest -m "not slow"   # Skip slow tests
```

## 📂 File Paths Convention

### Always use full paths in code/comments

✅ **Correct:**
```python
# See docs/PLAN.md for details
# Configuration in docs/CONFIG.md
# Refer to docs/ARCHITECTURE.md
```

❌ **Incorrect:**
```python
# See PLAN.md
# Configuration in CONFIG.md
```

### Exceptions (files in root):
- `README.md`
- `config.yaml.example`
- `SETUP_COMPLETE.md`

## 📝 Git Commit Format

```bash
type(scope): description

Types:
  feat     - New feature
  fix      - Bug fix
  docs     - Documentation
  style    - Formatting
  refactor - Code refactoring
  test     - Tests
  chore    - Maintenance

Examples:
  feat(cli): add cleanup command
  fix(aptly): handle missing repo
  docs(readme): update installation
  test(config): add validation tests
```

## 🏗️ Module Structure

```
config.py (no dependencies)
    ↓
    ├─→ aptly.py
    ├─→ gpg.py
    ├─→ retention.py
    └─→ utils.py
            ↓
        cli.py (uses all)
```

## 🔍 Common Patterns

### Config Loading
```python
config = Config("config.yaml")
aptly_root = config.get_aptly_root(codename)
```

### Aptly Operations
```python
manager = AptlyManager(config)
manager.add_packages(codename, component, packages)
```

### Error Handling
```python
try:
    result = operation()
except SpecificError as e:
    logger.error(f"Failed: {e}")
    raise
```

### Testing
```python
def test_function(mocker):
    """Test with mock."""
    mock = mocker.patch("subprocess.run")
    result = function()
    mock.assert_called_once()
```

## 📦 Project Structure

```
repomanager/
├── docs/                      # All documentation
├── .cursorrules/              # Cursor AI rules
├── .github/workflows/         # GitHub Actions
├── repomanager/               # Python package
│   ├── __init__.py
│   ├── cli.py                # CLI entry point
│   ├── config.py             # Configuration
│   ├── aptly.py              # Aptly wrapper
│   ├── retention.py          # Retention logic
│   ├── gpg.py                # GPG operations
│   └── utils.py              # Utilities
├── tests/                     # Tests
├── config.yaml.example        # Config template
├── requirements.txt           # Dependencies
├── setup.py                   # Installation
├── pyproject.toml             # Modern config
└── README.md                  # Main page
```

## 🚀 Quick Start for AI

### New to project?
1. Read [.cursorrules/README.md](.cursorrules/README.md)
2. Read [docs/QUICKSTART.md](../docs/QUICKSTART.md)
3. Check [docs/PLAN.md](../docs/PLAN.md)

### Adding code?
1. Check [code-style.md](code-style.md)
2. Write tests ([testing.md](testing.md))
3. Follow patterns ([architecture.md](architecture.md))

### Before commit?
```bash
make check-all
```

## 🔗 External Links

### Technologies
- [aptly docs](https://www.aptly.info/doc/overview/)
- [pytest docs](https://docs.pytest.org/)
- [Black docs](https://black.readthedocs.io/)
- [mypy docs](https://mypy.readthedocs.io/)

### Standards
- [PEP 8](https://pep8.org/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 📞 Getting Help

- **Issues**: https://github.com/jethome/repomanager/issues
- **Discussions**: https://github.com/jethome/repomanager/discussions
- **Email**: support@jethome.ru
- **Docs**: docs/README.md
- **Help**: `make help`

## 💡 Tips for AI

1. **Always add tests** when writing new code
2. **Use full paths** when referencing docs (e.g., `docs/PLAN.md`)
3. **Run `make check-all`** before suggesting code is ready
4. **Follow existing patterns** in codebase
5. **Check [pitfalls.md](pitfalls.md)** for common mistakes
6. **Security first** - see [security.md](security.md)

## 🎯 Coverage Requirements

- **Overall**: 80% minimum для MVP (goal: 85%+)
- **Critical modules**: 85%+ обязательно (config, aptly)
- **GPG, Utils, CLI**: 80%+
- **New code**: must have tests (TDD preferred)

## ⚙️ Configuration Paths

- **Repository**: `./config.yaml`
- **Server**: `/etc/repomanager/config.yaml`
- **Priority**: CLI args > Server > Repository > Defaults

## 🔐 Security Checklist

- [ ] Never log passphrases or secrets
- [ ] Validate all user inputs
- [ ] Use pathlib for paths (prevents traversal)
- [ ] Use list form for subprocess (no shell=True)
- [ ] Cleanup imported GPG keys (GitHub Actions)
- [ ] Set restrictive file permissions (600 for secrets)

## ✅ Pre-Commit Checklist

- [ ] Code formatted (Black)
- [ ] No lint errors (flake8)
- [ ] No type errors (mypy)
- [ ] Tests passing (pytest)
- [ ] Coverage maintained
- [ ] No trailing spaces
- [ ] Docstrings added
- [ ] Type hints added
- [ ] Documentation updated

## See All Rules

- [README.md](README.md) - Start here (overview)
- [mvp-requirements.md](mvp-requirements.md) - 🎯 MVP scope & requirements
- [code-style.md](code-style.md) - Code style
- [testing.md](testing.md) - Testing
- [development.md](development.md) - Workflow
- [architecture.md](architecture.md) - Architecture
- [aptly-integration.md](aptly-integration.md) - Aptly patterns
- [documentation.md](documentation.md) - Docs guidelines
- [error-handling.md](error-handling.md) - Error handling
- [security.md](security.md) - Security
- [pitfalls.md](pitfalls.md) - Common mistakes

## 🎯 Current Phase

**Phase 1**: Core Modules (config, utils, aptly base)
**Next**: Step 1.1 - Config Module
**Progress**: ~14% (Phase 0 done)

Track in: docs/IMPLEMENTATION_PLAN.md

