# Code Style Guidelines

## 🏁 Current Development Phase

**Phase 1**: Core Modules (config, utils, aptly base)
**Next Step**: Step 1.1 - Config Module
**См.**: docs/IMPLEMENTATION_PLAN.md для деталей

## Python Code Style

### Основные требования

- **Indentation**: 4 spaces (NOT tabs) - обязательно для Python файлов
- **Line length**: 88 characters (Black default)
- **Formatter**: Black (обязательно)
- **Linter**: flake8 (обязательно)
- **Type checker**: mypy (обязательно)
- **Docstrings**: Google style (обязательно)
- **Type hints**: обязательны для всех публичных функций и методов

### Code Quality Checklist

- ✅ Всегда удалять trailing spaces (пробелы в конце строк)
- ✅ Обязательное использование type hints
- ✅ Docstrings для всех публичных классов и функций
- ✅ Imports в порядке: stdlib → third-party → local
- ✅ Использовать f-strings вместо .format() или %
- ✅ Prefer pathlib.Path over os.path
- ✅ No print() - use logging instead

## Example Function Structure

```python
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def function_name(
    arg1: str,
    arg2: int,
    optional_arg: Optional[str] = None
) -> bool:
    """Brief description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        optional_arg: Description of optional_arg

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    logger.info(f"Processing {arg1}")
    # Implementation
    return True
```

## Imports Organization

```python
# 1. Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 2. Third-party imports
import yaml
import click
from debian.deb822 import Deb822

# 3. Local application imports
from repomanager.config import Config
from repomanager.utils import setup_logging
```

## Naming Conventions

### Variables and Functions
- `snake_case` для переменных и функций
- `UPPER_CASE` для констант
- Descriptive names, избегать abbreviations

```python
# Good
user_count = 10
MAX_RETRIES = 3

def get_package_info(package_name: str) -> Dict[str, Any]:
    pass

# Bad
uc = 10
max_r = 3

def gpkg(pn):
    pass
```

### Classes
- `PascalCase` для классов
- Descriptive names

```python
# Good
class AptlyManager:
    pass

class RetentionPolicy:
    pass

# Bad
class aptly_manager:
    pass

class RP:
    pass
```

### Private Members
- Prefix с `_` для private/internal

```python
class MyClass:
    def public_method(self):
        pass

    def _private_method(self):
        pass

    def _internal_helper(self):
        pass
```

## Docstrings (Google Style)

### Module Docstring
```python
"""Module for managing Debian repositories.

This module provides functionality to manage aptly-based Debian repositories
with support for multiple distributions and architectures.
"""
```

### Class Docstring
```python
class AptlyManager:
    """Manager for aptly repository operations.

    Provides high-level interface for creating, managing, and publishing
    Debian repositories using aptly.

    Attributes:
        config: Configuration object
        logger: Logger instance
    """
```

### Function Docstring
```python
def add_packages(
    codename: str,
    component: str,
    packages: List[str]
) -> bool:
    """Add packages to repository.

    Adds specified packages to the given repository and creates
    a new snapshot for atomic publishing.

    Args:
        codename: Distribution codename (e.g., 'bookworm')
        component: Repository component (e.g., 'jethome-tools')
        packages: List of package file paths

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If codename or component is invalid
        FileNotFoundError: If package files don't exist
        RuntimeError: If aptly operation fails

    Example:
        >>> manager.add_packages('bookworm', 'main', ['pkg1.deb'])
        True
    """
```

## Type Hints

### Basic Types
```python
from typing import List, Dict, Optional, Union, Any

def process_data(
    data: str,
    count: int,
    options: Optional[Dict[str, Any]] = None
) -> List[str]:
    pass
```

### Custom Types
```python
from typing import TypedDict, NamedTuple
from dataclasses import dataclass

@dataclass
class PackageInfo:
    name: str
    version: str
    architecture: str

RetentionConfig = Dict[str, int]
```

### Return Types
```python
# Simple return
def get_name() -> str:
    return "name"

# Multiple return types
def get_value() -> Optional[int]:
    return None

# No return
def log_message(msg: str) -> None:
    print(msg)
```

## String Formatting

### Always use f-strings
```python
# Good
name = "John"
age = 30
message = f"Hello, {name}! You are {age} years old."

# Bad
message = "Hello, %s! You are %d years old." % (name, age)
message = "Hello, {}! You are {} years old.".format(name, age)
```

## File Paths

### Use pathlib.Path
```python
from pathlib import Path

# Good
config_path = Path("/etc/repomanager/config.yaml")
if config_path.exists():
    with config_path.open() as f:
        data = f.read()

# Bad
import os.path
config_path = "/etc/repomanager/config.yaml"
if os.path.exists(config_path):
    with open(config_path) as f:
        data = f.read()
```

## Logging

### Use logging module, not print()
```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info("Processing packages")
logger.error(f"Failed to add package: {error}")
logger.debug(f"Package metadata: {metadata}")

# Bad
print("Processing packages")
print(f"Error: {error}")
```

## Tools Commands

```bash
# Format code
black repomanager/ tests/

# Check formatting
black --check repomanager/ tests/

# Lint
flake8 repomanager/ tests/

# Type check
mypy repomanager/

# All checks
make check-all
```

## Configuration Files

### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = .git,__pycache__,build,dist,venv
```

### pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.mypy]
python_version = "3.8"
warn_return_any = true
disallow_untyped_defs = true
```

## See Also

- [testing.md](testing.md) - Testing guidelines
- [development.md](development.md) - Development workflow
- [pitfalls.md](pitfalls.md) - Common mistakes to avoid


