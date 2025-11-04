# Development Workflow

## Before Committing

### Required Checks (обязательно!)

```bash
# 1. Format code
make format
# or
black repomanager/ tests/

# 2. Run linter
make lint
# or
flake8 repomanager/ tests/

# 3. Type check
make type-check
# or
mypy repomanager/

# 4. Run tests
make test
# or
pytest

# 5. Check coverage
make test-coverage

# 6. All checks at once (recommended)
make check-all
```

### Pre-commit Checklist

- [ ] Code formatted with Black
- [ ] No flake8 violations
- [ ] No mypy type errors
- [ ] All tests passing
- [ ] Coverage >= 70% (new code covered)
- [ ] No trailing spaces
- [ ] Docstrings added for new public functions
- [ ] Type hints added for new functions
- [ ] Tests added for new functionality
- [ ] Documentation updated if needed

## Git Workflow

### Branch Naming

```bash
# Feature branches
feature/add-cleanup-command
feature/gpg-integration

# Bug fixes
fix/aptly-snapshot-error
fix/config-merge-bug

# Documentation
docs/update-architecture
docs/add-workflows-guide

# Refactoring
refactor/config-module
refactor/improve-error-handling
```

### Commit Messages

#### Format: Conventional Commits

```
type(scope): description

[optional body]

[optional footer]
```

#### Types
- `feat`: новая функциональность
- `fix`: исправление бага
- `docs`: изменения в документации
- `style`: форматирование, missing semicolons, и т.д.
- `refactor`: refactoring кода
- `test`: добавление или исправление тестов
- `chore`: обновление build tasks, package manager configs, и т.д.

#### Examples

**Feature:**
```
feat(cli): add cleanup command with dry-run support

- Add cleanup subcommand to CLI
- Implement dry-run mode
- Add tests for cleanup functionality
```

**Fix:**
```
fix(aptly): handle missing repository gracefully

Fixes #42

Previously, missing repository caused uncaught exception.
Now returns clear error message and suggests creating repo.
```

**Documentation:**
```
docs(readme): update installation instructions

- Add Python 3.12 support
- Update apt

ly installation steps
- Add troubleshooting section
```

**Refactoring:**
```
refactor(config): simplify config merging logic

- Extract merge logic to separate method
- Add type hints
- Improve test coverage
```

**Tests:**
```
test(retention): add tests for edge cases

- Test with empty package list
- Test with single package
- Test with all packages older than retention
```

### Commit Best Practices

1. ✅ **Atomic commits** - один логический change на commit
2. ✅ **Clear messages** - описывай ЧТО и ПОЧЕМУ, не КАК
3. ✅ **Reference issues** - используй `Fixes #123` или `Closes #123`
4. ✅ **Keep commits small** - легче review, легче revert
5. ✅ **Test before commit** - коммит только working code

## Pull Request Workflow

### Creating PR

1. **Убедись что код готов**:
   ```bash
   make check-all
   ```

2. **Push branch**:
   ```bash
   git push origin feature/my-feature
   ```

3. **Create PR** на GitHub:
   - Clear title (conventional commits format)
   - Description with context
   - Link related issues
   - Add labels if applicable

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Coverage maintained/improved

## Documentation
- [ ] Documentation updated
- [ ] Docstrings added

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added
- [ ] Documentation updated

## Related Issues
Fixes #123
Closes #456
```

### PR Review Process

**GitHub Actions автоматически проверят**:
- ✅ Code formatting (Black)
- ✅ Linting (flake8)
- ✅ Type checking (mypy)
- ✅ Tests (pytest)
- ✅ Coverage
- ✅ Security (Bandit)
- ✅ Documentation

**Если проверки не прошли**:
- Посмотри комментарий бота с ошибками
- Исправь локально
- Или используй `/fix-ci` в комментарии для auto-fix

### Using /fix-ci Command

В комментарии к PR напиши:
```
/fix-ci
```

Автоматически применится:
- Black formatting
- isort (import sorting)
- Удаление trailing spaces
- Commit с исправлениями

## Development Environment

### Initial Setup

```bash
# Clone repository
git clone https://github.com/jethome/repomanager.git
cd repomanager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e ".[dev]"

# Verify setup
make check-all
```

### Daily Workflow

```bash
# 1. Update main
git checkout main
git pull

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes
vim repomanager/module.py

# 4. Run checks frequently
make test

# 5. Commit when ready
git add repomanager/module.py tests/test_module.py
git commit -m "feat(module): add new functionality"

# 6. Final check before push
make check-all

# 7. Push and create PR
git push origin feature/my-feature
```

### IDE Setup

#### VS Code / Cursor
`.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true
}
```

#### PyCharm
- Enable Black formatter
- Enable flake8 inspection
- Enable mypy inspection
- Enable "Remove trailing spaces on save"

## Working with Documentation

### When to Update Docs

- **Новая функциональность** → README.md + docs/IMPLEMENTATION_STEPS.md
- **Изменение API** → docs/IMPLEMENTATION_STEPS.md
- **Новая конфигурация** → docs/CONFIG.md + config.yaml.example
- **Архитектурные изменения** → docs/ARCHITECTURE.md
- **Новый workflow** → docs/WORKFLOWS.md
- **Прогресс задач** → docs/TODO.md

### Documentation Updates

```bash
# Edit documentation
vim docs/CONFIG.md

# Commit with docs: prefix
git commit -m "docs(config): add new retention policy options"

# GitHub Actions автоматически проверит документацию
```

## Makefile Commands

```bash
# Show all available commands
make help

# Development
make install        # Install package
make install-dev    # Install with dev dependencies

# Testing
make test           # Run tests
make test-verbose   # Run tests with verbose output
make test-coverage  # Run tests with coverage

# Code quality
make format         # Format code with black
make format-check   # Check formatting without changes
make lint           # Run flake8
make type-check     # Run mypy

# All checks
make check-all      # Run all checks (recommended before commit)

# Cleanup
make clean          # Remove build artifacts
```

## Debugging

### Debug Tests
```bash
# Run specific test with prints
pytest tests/test_module.py::test_function -s

# Run with debugger
pytest tests/test_module.py::test_function --pdb

# Run with verbose output
pytest -vv
```

### Debug Application
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

### Debug with logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In code
logger.debug(f"Variable value: {value}")
```

## Release Process

### Version Bump

1. Update version in `repomanager/__init__.py`
2. Update `docs/CHANGELOG.md`
3. Commit: `chore: bump version to 0.2.0`
4. Tag: `git tag -a v0.2.0 -m "Version 0.2.0"`
5. Push: `git push origin main --tags`

### Creating Release

1. GitHub → Releases → Create new release
2. Choose tag
3. Write release notes (from CHANGELOG)
4. Publish release

## Troubleshooting

### Import errors in tests
```bash
# Reinstall in editable mode
pip install -e .
```

### Flake8/mypy cache issues
```bash
# Clean cache
make clean
rm -rf .mypy_cache/ .pytest_cache/
```

### Test failures after merge
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests
pytest
```

## See Also

- [code-style.md](code-style.md) - Code style guidelines
- [testing.md](testing.md) - Testing requirements
- [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) - Full development guide
- [docs/WORKFLOWS.md](../docs/WORKFLOWS.md) - GitHub Actions workflows


