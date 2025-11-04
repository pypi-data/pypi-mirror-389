# Documentation Guidelines

## When to Update Documentation

- **Новая функциональность** → README.md + docs/IMPLEMENTATION_STEPS.md
- **Изменение API** → docs/IMPLEMENTATION_STEPS.md
- **Новая конфигурация** → docs/CONFIG.md + config.yaml.example
- **Архитектурные изменения** → docs/ARCHITECTURE.md
- **Новый GitHub workflow** → docs/WORKFLOWS.md
- **Прогресс задач** → docs/TODO.md

## Documentation Structure

```
docs/
├── README.md                  # Навигация по всей документации
├── IMPLEMENTATION_PLAN.md     # 🎯 Финальный план с чекбоксами (START HERE!)
├── PHASES_OVERVIEW.md         # Визуальный обзор фаз и timeline
├── QUICKSTART.md              # Быстрый старт за 5 минут
├── APT_CONFIGURATION.md       # Настройка APT для клиентских систем
├── DUAL_FORMAT.md             # Поддержка двух форматов URL (техническая)
├── ARCHITECTURE.md            # Архитектурные решения
├── CONFIG.md                  # Детальное описание конфигурации
├── IMPLEMENTATION_STEPS.md    # Примеры кода для каждого модуля
├── DEVELOPMENT.md             # Руководство для разработчиков
├── WORKFLOWS.md               # GitHub Actions workflows
├── PROJECT_STRUCTURE.md       # Структура проекта и модулей
├── TODO.md                    # Checklist задач
├── SUMMARY.md                 # Краткое резюме и прогресс
├── CHANGELOG.md               # История изменений
└── PLAN.md                    # Оригинальный план (reference)
```

## File Paths Convention

### В коде и комментариях всегда используй полные пути

✅ **Правильно:**
```python
# See docs/PLAN.md for implementation plan
# Configuration details in docs/CONFIG.md
# Refer to docs/ARCHITECTURE.md for design
```

❌ **Неправильно:**
```python
# See PLAN.md
# Configuration details in CONFIG.md
```

### Исключения (файлы в корне):
- `README.md` (главная страница проекта)
- `config.yaml.example` (шаблон конфигурации)
- `SETUP_COMPLETE.md` (информация о setup)

## Docstring Guidelines

### Module Docstring
```python
"""Debian repository management module.

This module provides functionality to manage aptly-based Debian repositories
with support for multiple distributions, architectures, and components.

Example:
    Basic usage::

        from repomanager import AptlyManager, Config

        config = Config("config.yaml")
        manager = AptlyManager(config)
        manager.add_packages("bookworm", "main", ["pkg.deb"])
"""
```

### Class Docstring (Google Style)
```python
class AptlyManager:
    """Manager for aptly repository operations.

    Provides high-level interface for creating, managing, and publishing
    Debian repositories using aptly with snapshot-based atomic updates.

    Attributes:
        config: Configuration object containing aptly settings
        logger: Logger instance for this manager

    Example:
        >>> config = Config("config.yaml")
        >>> manager = AptlyManager(config)
        >>> manager.create_repo("bookworm", "jethome-tools")
        True
    """
```

### Function Docstring
```python
def add_packages(
    codename: str,
    component: str,
    packages: List[str],
    dry_run: bool = False
) -> bool:
    """Add packages to repository with atomic snapshot publication.

    Adds specified packages to the repository, creates a new snapshot,
    and atomically switches the published repository to the new snapshot.

    Args:
        codename: Distribution codename (e.g., 'bookworm', 'noble')
        component: Repository component (e.g., 'jethome-tools')
        packages: List of .deb file paths to add
        dry_run: If True, simulate without making changes

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If codename or component is invalid
        FileNotFoundError: If package files don't exist
        AptlyError: If aptly operation fails

    Example:
        >>> manager.add_packages(
        ...     "bookworm",
        ...     "jethome-tools",
        ...     ["/path/to/package.deb"]
        ... )
        True

    Note:
        This operation is atomic - the repository is updated via snapshot
        switch, ensuring no partial updates are visible to users.

    See Also:
        - docs/ARCHITECTURE.md for snapshot workflow
        - docs/IMPLEMENTATION_STEPS.md for code examples
    """
```

## README.md Guidelines

### Structure
```markdown
# Project Title

Brief description

## Features
- Feature 1
- Feature 2

## Requirements
...

## Installation
...

## Usage
...

## Documentation
- Link to docs/

## License
```

### Linking to docs/
```markdown
## Documentation

- [Quick Start](docs/QUICKSTART.md) - Get started in 5 minutes
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Configuration](docs/CONFIG.md) - Config reference
- [Development](docs/DEVELOPMENT.md) - Developer guide
```

## Comment Guidelines

### Inline Comments
```python
# Good: Explains WHY
packages.sort(reverse=True)  # Sort newest first for retention policy

# Bad: Explains WHAT (obvious from code)
i = i + 1  # Increment i
```

### TODO Comments
```python
# TODO(username): Add support for multiple architectures
# FIXME(username): Handle edge case when package list is empty
# NOTE: This assumes aptly version >= 1.5.0
```

## Documentation Updates in Workflow

### Git Commit Messages
```bash
# Good
git commit -m "docs(config): add retention policy examples"
git commit -m "docs(readme): update installation steps for Python 3.12"

# Bad
git commit -m "update docs"
git commit -m "fix"
```

### Pull Requests
Always update docs in the same PR as code changes:
- New feature → update docs/IMPLEMENTATION_STEPS.md + README.md
- Config change → update docs/CONFIG.md + config.yaml.example
- Bug fix → update docs/CHANGELOG.md

## GitHub Actions Automation

Workflow `docs-update.yml` автоматически:
- Проверяет недокументированные модули
- Проверяет недокументированные config опции
- Отслеживает прогресс TODO
- Комментирует PR с отчетом

См. [docs/WORKFLOWS.md](../docs/WORKFLOWS.md) для деталей.

## Quick Reference

### For users
- **docs/README.md** - start here for navigation
- **docs/QUICKSTART.md** - quick 5-minute start
- **README.md** - main project page

### For developers
- **docs/PLAN.md** - implementation plan
- **docs/IMPLEMENTATION_STEPS.md** - code examples
- **docs/DEVELOPMENT.md** - developer workflow

### For DevOps
- **docs/WORKFLOWS.md** - GitHub Actions guide
- **docs/CONFIG.md** - configuration reference

## See Also

- [code-style.md](code-style.md) - Code style (includes docstring examples)
- [development.md](development.md) - When to update docs in workflow
- [docs/README.md](../docs/README.md) - Full documentation index


