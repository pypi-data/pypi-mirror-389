# Architecture Guidelines

## Key Principles

### 0. Dual Format Support (Critical!)
**Поддержка двух форматов URL одновременно** (Phase 5):

**Старый формат:**
```bash
deb http://repo.site.com bookworm jethome-bookworm
```

**Новый формат:**
```bash
deb http://repo.site.com/bookworm jethome-bookworm main
```

**Реализация**: Через symlinks, автоматически создаются при publish.
**Почему важно**: Куча старых клиентов которые не обновятся.
**См.**: docs/DUAL_FORMAT.md для технических деталей.

### 1. Separation of Concerns
Каждый модуль отвечает за свою область:

**MVP Modules (Phases 1-6):**
- **config.py**: загрузка и управление конфигурацией
- **utils.py**: вспомогательные функции (logging, parsing, version compare)
- **aptly.py**: обертка над aptly CLI, все операции с репозиториями
- **gpg.py**: операции с GPG ключами и signing
- **cli.py**: CLI interface, парсинг аргументов, routing команд

**Extended Modules (Phase 8):**
- **retention.py**: логика retention policies (не входит в MVP)

### 2. Dependency Injection
Передавай Config в конструкторы, не создавай глобальные instances:

```python
# Good
class AptlyManager:
    def __init__(self, config: Config):
        self.config = config

# Usage
config = Config("config.yaml")
manager = AptlyManager(config)

# Bad
class AptlyManager:
    def __init__(self):
        self.config = Config("config.yaml")  # Hard-coded!
```

### 3. Immutability
Используй dataclasses для data objects:

```python
from dataclasses import dataclass

@dataclass
class PackageInfo:
    """Package metadata."""
    name: str
    version: str
    architecture: str
    file_path: str

# RetentionPolicy - Phase 8 (не MVP)
# @dataclass
# class RetentionPolicy:
#     min_versions: int
#     max_age_days: int
```

### 4. Error Handling
Всегда обрабатывай ошибки subprocess и внешних вызовов:

```python
try:
    result = subprocess.run(cmd, check=True, capture_output=True)
    return result.stdout
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e}")
    raise RuntimeError(f"Operation failed: {e.stderr}") from e
```

### 5. Logging
Используй logging, не print():

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing packages")
logger.error(f"Failed: {error}")
logger.debug(f"Details: {details}")
```

### 6. Force Creation & Auto-Create
**Важно для MVP!**

**--force опция**: Позволяет recreate репозиторий если уже существует
```python
def create_repo(self, codename: str, component: str, force: bool = False):
    if self.repo_exists(codename, component):
        if force:
            logger.warning(f"Repo exists, recreating (--force)")
            self.delete_repo(codename, component)
        else:
            raise ValueError(f"Repo already exists: {codename}/{component}")
    # Create repo...
```

**auto_create config**: Автоматически создает репо при добавлении пакетов
```yaml
repositories:
  auto_create: true  # Создать репо автоматически если не существует
```

**См.**: docs/IMPLEMENTATION_PLAN.md Phase 2 и Phase 3 для деталей

## Module Dependencies Flow

### MVP Modules (Phases 1-6)
```
config.py (базовый, без зависимостей)
    ↓
    ├─→ utils.py (независимый, общие утилиты)
    │
    ├─→ aptly.py (зависит от config)
    │       ↓
    │   используется в cli.py для repo operations
    │
    └─→ gpg.py (зависит от config)
            ↓
        используется в aptly.py для signing
            ↓
        cli.py (использует все модули, entry point)
```

### Extended Modules (Phase 8 - не MVP)
```
retention.py (зависит от config, utils)
    ↓
используется в cli.py для cleanup command
```

### Dependency Rules

1. **config.py** - НЕ должен импортировать другие модули проекта
2. **utils.py** - НЕ должен импортировать другие модули проекта
3. **aptly.py, gpg.py** - могут импортировать config и utils
4. **retention.py** (Phase 8) - может импортировать config и utils
5. **cli.py** - может импортировать все модули (entry point)

## Module Responsibilities

### config.py
```python
class Config:
    """Configuration management."""

    def load(self, path: str) -> None:
        """Load configuration from YAML."""

    def merge(self, other: Dict) -> None:
        """Merge another configuration."""

    def get_aptly_root(self, codename: str) -> str:
        """Get aptly root for codename."""

    def get_retention_policy(self, component: str) -> RetentionPolicy:
        """Get retention policy for component."""
```

**Ответственность:**
- Загрузка YAML конфигурации
- Мерджинг конфигов (repo + server)
- Валидация параметров
- Доступ к настройкам

**НЕ должен:**
- Выполнять aptly команды
- Выполнять GPG операции
- Работать с файловой системой (кроме загрузки конфига)

### aptly.py
```python
class AptlyManager:
    """Wrapper around aptly CLI."""

    def create_repo(self, codename: str, component: str) -> bool:
        """Create repository."""

    def add_packages(self, codename: str, component: str, packages: List[str]) -> bool:
        """Add packages to repository."""

    def create_snapshot(self, codename: str, component: str) -> str:
        """Create snapshot from repo."""

    def publish_snapshot(self, codename: str, component: str, snapshot: str) -> bool:
        """Publish or switch snapshot."""
```

**Ответственность:**
- Все операции с aptly
- Создание/удаление репозиториев
- Управление snapshots
- Публикация репозиториев

**НЕ должен:**
- Парсить CLI аргументы
- Делать retention logic
- Прямо работать с GPG (использует gpg.py)

### retention.py (Phase 8 - не MVP)
```python
@dataclass
class RetentionPolicy:
    min_versions: int
    max_age_days: int

    def get_packages_to_remove(self, packages: List[PackageInfo]) -> List[PackageInfo]:
        """Determine packages to remove."""
```

**Статус**: Phase 8 (следующая итерация)

**Ответственность:**
- Логика retention policies
- Определение пакетов для удаления
- Группировка по версиям

**НЕ должен:**
- Удалять пакеты (это делает aptly.py)
- Парсить CLI аргументы
- Выполнять aptly команды

**См.**: docs/IMPLEMENTATION_PLAN.md Phase 8 для деталей

### cli.py
```python
@click.group()
def cli():
    """Entry point."""

@cli.command()
@click.option("--codename")
def add(codename, ...):
    """Add packages command."""
    config = Config()
    manager = AptlyManager(config)
    # Implementation
```

**Ответственность:**
- CLI interface (click/argparse)
- Парсинг аргументов
- Routing команд
- Координация модулей
- User-facing error messages

**НЕ должен:**
- Реализовывать бизнес-логику (делегирует модулям)
- Прямо работать с subprocess (использует модули)

## Design Patterns

### Factory Pattern (для Config)
```python
class Config:
    @classmethod
    def from_file(cls, path: str) -> 'Config':
        """Create config from file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(data)

    @classmethod
    def from_default(cls) -> 'Config':
        """Create config with defaults."""
        return cls(cls.DEFAULT_CONFIG)
```

### Builder Pattern (для сложных операций)
```python
class SnapshotBuilder:
    """Build and publish snapshot atomically."""

    def __init__(self, manager: AptlyManager):
        self.manager = manager

    def add_packages(self, packages: List[str]) -> 'SnapshotBuilder':
        self.manager.add_packages(...)
        return self

    def create_snapshot(self, name: str) -> 'SnapshotBuilder':
        self.manager.create_snapshot(...)
        return self

    def publish(self) -> bool:
        return self.manager.publish_snapshot(...)
```

### Strategy Pattern (для retention policies)
```python
class RetentionStrategy(ABC):
    @abstractmethod
    def should_remove(self, package: PackageInfo) -> bool:
        pass

class AgeBasedRetention(RetentionStrategy):
    def should_remove(self, package: PackageInfo) -> bool:
        return package.age > self.max_age_days

class VersionBasedRetention(RetentionStrategy):
    def should_remove(self, package: PackageInfo) -> bool:
        return package.version_rank > self.min_versions
```

## Error Handling Strategy

### Error Hierarchy
```python
class RepomanagerError(Exception):
    """Base exception for repomanager."""

class ConfigError(RepomanagerError):
    """Configuration related errors."""

class AptlyError(RepomanagerError):
    """Aptly operation errors."""

class GPGError(RepomanagerError):
    """GPG operation errors."""
```

### Error Propagation
```python
# Low-level (aptly.py)
def _run_aptly(self, args: List[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Aptly command failed: {e}")
        raise AptlyError(f"Command failed: {e.stderr}") from e

# Mid-level (aptly.py)
def create_repo(self, codename: str, component: str) -> bool:
    try:
        self._run_aptly(["repo", "create", ...])
        return True
    except AptlyError:
        logger.error(f"Failed to create repo {component}")
        raise

# High-level (cli.py)
@cli.command()
def create_repo(codename, component):
    try:
        manager.create_repo(codename, component)
        click.echo("Repository created successfully")
    except AptlyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
```

## Performance Considerations

### Minimize aptly calls
```python
# Bad: multiple calls
for package in packages:
    aptly.add_package(package)  # N calls

# Good: bulk operation
aptly.add_packages(packages)  # 1 call
```

### Cache expensive operations
```python
class AptlyManager:
    def __init__(self, config: Config):
        self.config = config
        self._package_cache: Dict[str, List[PackageInfo]] = {}

    def list_packages(self, codename: str, component: str) -> List[PackageInfo]:
        cache_key = f"{codename}/{component}"
        if cache_key not in self._package_cache:
            self._package_cache[cache_key] = self._fetch_packages(...)
        return self._package_cache[cache_key]
```

### Log timing for critical operations
```python
import time

def add_packages(self, ...):
    start = time.time()
    logger.info(f"Adding {len(packages)} packages...")

    # Operation
    result = self._add_packages_internal(...)

    elapsed = time.time() - start
    logger.info(f"Added packages in {elapsed:.2f}s")
    return result
```

## Testing Strategy

### Unit tests для каждого модуля
- config.py → tests/test_config.py
- aptly.py → tests/test_aptly.py
- Моки для subprocess и file I/O

### Integration tests для workflows
- Полный цикл add packages
- Полный цикл cleanup
- С реальным aptly (CI only)

## See Also

- [aptly-integration.md](aptly-integration.md) - Aptly patterns
- [error-handling.md](error-handling.md) - Error handling patterns
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Full architecture document


