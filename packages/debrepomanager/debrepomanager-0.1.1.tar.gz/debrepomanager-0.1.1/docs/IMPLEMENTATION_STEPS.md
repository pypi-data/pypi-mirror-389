# Пошаговая инструкция реализации

Детальное руководство по реализации каждого модуля с примерами кода и API.

## Порядок реализации

### Этап 1: Базовые модули (можно делать параллельно)

#### 1.1 Config Module (`repomanager/config.py`)

**Цель**: Загрузка и управление конфигурацией из YAML файлов.

**API**:
```python
class Config:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config, optionally load from path."""

    def load(self, config_path: str) -> None:
        """Load configuration from YAML file."""

    def load_default(self) -> None:
        """Load default configuration."""

    def merge(self, other_config: Dict[str, Any]) -> None:
        """Merge another configuration (overrides current)."""

    @property
    def aptly_root_base(self) -> str:
        """Get aptly root base directory."""

    @property
    def publish_base(self) -> str:
        """Get publish base directory."""

    def get_aptly_root(self, codename: str) -> str:
        """Get aptly root for specific codename."""

    def get_retention_policy(self, component: str) -> 'RetentionPolicy':
        """Get retention policy for component (with overrides)."""

    def get_codenames(self) -> List[str]:
        """Get list of supported codenames."""

    def get_components(self) -> List[str]:
        """Get list of components."""

    def get_architectures(self) -> List[str]:
        """Get list of architectures."""

    @property
    def gpg_key_id(self) -> str:
        """Get GPG key ID."""

    @property
    def auto_create_repos(self) -> bool:
        """Check if auto-creation is enabled."""
```

**Реализация**:
```python
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class Config:
    DEFAULT_CONFIG = {
        "aptly": {
            "root_base": "/srv/aptly",
            "publish_base": "/srv/repo/public",
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
        },
        "gpg": {
            "key_id": "",
            "use_agent": True,
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self.load_default()

        if config_path:
            self.load(config_path)

        # Try to load server config
        server_config_path = "/etc/repomanager/config.yaml"
        if Path(server_config_path).exists():
            self.load(server_config_path, merge=True)

    def load_default(self) -> None:
        """Load default configuration."""
        self._config = self.DEFAULT_CONFIG.copy()

    def load(self, config_path: str, merge: bool = False) -> None:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            loaded_config = yaml.safe_load(f)

        if merge:
            self._merge_dict(self._config, loaded_config)
        else:
            self._config = loaded_config

    def _merge_dict(self, base: Dict, override: Dict) -> None:
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    # Property accessors...
    @property
    def aptly_root_base(self) -> str:
        return self._config["aptly"]["root_base"]

    # ... остальные property и методы
```

**Тесты** (`tests/test_config.py`):
```python
def test_load_default_config():
    config = Config()
    assert config.aptly_root_base == "/srv/aptly"

def test_load_from_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("aptly:\n  root_base: /custom")

    config = Config(str(config_file))
    assert config.aptly_root_base == "/custom"

def test_merge_configs():
    # Test merging server config over base config
    pass
```

---

#### 1.2 Utils Module (`repomanager/utils.py`)

**Цель**: Вспомогательные функции для работы с пакетами, версиями, логированием.

**API**:
```python
def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""

def parse_deb_metadata(deb_path: str) -> Dict[str, Any]:
    """Extract metadata from .deb file."""

def compare_versions(version1: str, version2: str) -> int:
    """Compare Debian package versions. Returns -1, 0, or 1."""

def find_deb_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all .deb files in directory."""

def get_package_age(deb_path: str) -> int:
    """Get package age in days based on modification time."""

class PackageInfo:
    """Information about a package."""
    name: str
    version: str
    architecture: str
    file_path: str
    modification_time: datetime
```

**Реализация**:
```python
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from debian.deb822 import Deb822
from debian.debfile import DebFile
import apt_pkg


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("repomanager")
    logger.setLevel(getattr(logging, level.upper()))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def parse_deb_metadata(deb_path: str) -> Dict[str, Any]:
    """Extract metadata from .deb file."""
    with DebFile(deb_path) as deb:
        control = deb.debcontrol()
        return {
            "Package": control.get("Package"),
            "Version": control.get("Version"),
            "Architecture": control.get("Architecture"),
            "Description": control.get("Description", ""),
        }


def compare_versions(version1: str, version2: str) -> int:
    """Compare Debian package versions."""
    apt_pkg.init_system()
    return apt_pkg.version_compare(version1, version2)


def find_deb_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all .deb files in directory."""
    path = Path(directory)
    pattern = "**/*.deb" if recursive else "*.deb"
    return [str(p) for p in path.glob(pattern)]
```

---

### Этап 2: Aptly Wrapper

#### 2.1 Aptly Module (`repomanager/aptly.py`)

**Цель**: Обертка над aptly CLI для управления репозиториями.

**API**:
```python
class AptlyManager:
    def __init__(self, config: Config):
        """Initialize aptly manager with configuration."""

    def create_repo(
        self,
        codename: str,
        component: str,
        architectures: Optional[List[str]] = None
    ) -> bool:
        """Create new local repository."""

    def repo_exists(self, codename: str, component: str) -> bool:
        """Check if repository exists."""

    def add_packages(
        self,
        codename: str,
        component: str,
        packages: List[str]
    ) -> bool:
        """Add packages to repository."""

    def create_snapshot(
        self,
        codename: str,
        component: str,
        snapshot_name: Optional[str] = None
    ) -> str:
        """Create snapshot from repo. Returns snapshot name."""

    def publish_snapshot(
        self,
        codename: str,
        component: str,
        snapshot_name: str,
        is_initial: bool = False
    ) -> bool:
        """Publish or switch to snapshot."""

    def list_packages(
        self,
        codename: str,
        component: str
    ) -> List[PackageInfo]:
        """List packages in repository."""

    def remove_packages(
        self,
        codename: str,
        component: str,
        packages: List[str]
    ) -> bool:
        """Remove packages from repository."""

    def cleanup_snapshots(
        self,
        codename: str,
        component: str,
        keep: int = 10
    ) -> int:
        """Remove old snapshots, keeping last N. Returns number removed."""

    def delete_repo(self, codename: str, component: str) -> bool:
        """Delete repository and all snapshots."""
```

**Пример реализации ключевых методов**:
```python
import subprocess
import json
from datetime import datetime
from typing import List, Optional


class AptlyManager:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("repomanager.aptly")

    def _get_repo_name(self, codename: str, component: str) -> str:
        """Get internal repository name."""
        return f"{component}-{codename}"

    def _run_aptly(
        self,
        args: List[str],
        codename: str,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Run aptly command with proper config."""
        aptly_root = self.config.get_aptly_root(codename)
        config_path = f"{aptly_root}/aptly.conf"

        cmd = ["aptly", "-config", config_path] + args

        self.logger.debug(f"Running: {' '.join(cmd)}")

        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=True
        )

    def create_repo(
        self,
        codename: str,
        component: str,
        architectures: Optional[List[str]] = None
    ) -> bool:
        """Create new local repository."""
        repo_name = self._get_repo_name(codename, component)

        if architectures is None:
            architectures = self.config.get_architectures()

        try:
            self._run_aptly(
                [
                    "repo", "create",
                    "-distribution", component,
                    "-component", "main",
                    "-architectures", ",".join(architectures),
                    repo_name
                ],
                codename
            )
            self.logger.info(f"Created repository: {repo_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create repo: {e}")
            return False

    def add_packages(
        self,
        codename: str,
        component: str,
        packages: List[str]
    ) -> bool:
        """Add packages to repository."""
        repo_name = self._get_repo_name(codename, component)

        try:
            self._run_aptly(
                ["repo", "add", repo_name] + packages,
                codename
            )
            self.logger.info(f"Added {len(packages)} packages to {repo_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to add packages: {e}")
            return False

    def create_snapshot(
        self,
        codename: str,
        component: str,
        snapshot_name: Optional[str] = None
    ) -> str:
        """Create snapshot from repo."""
        repo_name = self._get_repo_name(codename, component)

        if snapshot_name is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            snapshot_name = f"{repo_name}-{timestamp}"

        try:
            self._run_aptly(
                ["snapshot", "create", snapshot_name, "from", "repo", repo_name],
                codename
            )
            self.logger.info(f"Created snapshot: {snapshot_name}")
            return snapshot_name
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            raise

    def publish_snapshot(
        self,
        codename: str,
        component: str,
        snapshot_name: str,
        is_initial: bool = False
    ) -> bool:
        """Publish or switch to snapshot."""
        prefix = f"{codename}/{component}"

        try:
            if is_initial:
                # Initial publish
                self._run_aptly(
                    [
                        "publish", "snapshot",
                        "-distribution", component,
                        "-gpg-key", self.config.gpg_key_id,
                        snapshot_name,
                        prefix
                    ],
                    codename
                )
                self.logger.info(f"Published snapshot: {snapshot_name}")
            else:
                # Switch existing
                self._run_aptly(
                    [
                        "publish", "switch",
                        component,
                        prefix,
                        snapshot_name
                    ],
                    codename
                )
                self.logger.info(f"Switched to snapshot: {snapshot_name}")

            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to publish/switch: {e}")
            return False
```

**Тесты** (`tests/test_aptly.py`):
```python
def test_create_repo(mocker, mock_config):
    mock_run = mocker.patch("subprocess.run")
    manager = AptlyManager(mock_config)

    manager.create_repo("bookworm", "jethome-tools")

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "repo" in args
    assert "create" in args
```

---

### Этап 3: Retention Policy

#### 3.1 Retention Module (`repomanager/retention.py`)

**API**:
```python
@dataclass
class RetentionPolicy:
    min_versions: int
    max_age_days: int

    def get_packages_to_remove(
        self,
        packages: List[PackageInfo]
    ) -> List[PackageInfo]:
        """Determine which packages should be removed based on policy."""


def group_packages_by_name(packages: List[PackageInfo]) -> Dict[str, List[PackageInfo]]:
    """Group packages by name."""

def apply_retention_policy(
    packages: List[PackageInfo],
    policy: RetentionPolicy
) -> List[PackageInfo]:
    """Apply retention policy and return packages to remove."""
```

**Реализация**:
```python
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime, timedelta
from repomanager.utils import PackageInfo, compare_versions


@dataclass
class RetentionPolicy:
    min_versions: int
    max_age_days: int

    def get_packages_to_remove(
        self,
        packages: List[PackageInfo]
    ) -> List[PackageInfo]:
        """Determine packages to remove based on policy."""
        # Group by package name
        grouped = group_packages_by_name(packages)
        to_remove = []

        for pkg_name, pkg_versions in grouped.items():
            # Sort by version (newest first)
            sorted_versions = sorted(
                pkg_versions,
                key=lambda p: p.version,
                reverse=True,
                cmp=compare_versions
            )

            # Keep at least min_versions
            keep = sorted_versions[:self.min_versions]
            candidates = sorted_versions[self.min_versions:]

            # Remove candidates older than max_age_days
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

            for pkg in candidates:
                if pkg.modification_time < cutoff_date:
                    to_remove.append(pkg)

        return to_remove
```

---

### Этап 4: GPG Integration

#### 4.1 GPG Module (`repomanager/gpg.py`)

**API**:
```python
class GPGManager:
    def __init__(self, config: Config):
        """Initialize GPG manager."""

    def check_key_available(self, key_id: str) -> bool:
        """Check if GPG key is available in keyring."""

    def import_key(self, key_data: str, passphrase: str) -> bool:
        """Import GPG key (for GitHub Actions)."""

    def delete_key(self, key_id: str) -> bool:
        """Delete GPG key from keyring."""

    def test_signing(self) -> bool:
        """Test if signing works with configured key."""
```

---

### Этап 5: CLI

#### 5.1 CLI Module (`repomanager/cli.py`)

**Структура**:
```python
import click
from repomanager import Config, AptlyManager
from repomanager.utils import setup_logging


@click.group()
@click.option("--config", default=None, help="Config file path")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config, verbose):
    """Debian Repository Manager CLI."""
    ctx.ensure_object(dict)

    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    ctx.obj["config"] = Config(config)
    ctx.obj["logger"] = logger


@cli.command()
@click.option("--codename", required=True)
@click.option("--component", required=True)
@click.option("--packages", multiple=True)
@click.option("--package-dir")
@click.pass_context
def add(ctx, codename, component, packages, package_dir):
    """Add packages to repository."""
    config = ctx.obj["config"]
    manager = AptlyManager(config)

    # Implementation...


@cli.command()
@click.option("--codename", required=True)
@click.option("--component", required=True)
@click.pass_context
def create_repo(ctx, codename, component):
    """Create new repository."""
    # Implementation...


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
```

---

### Этап 6: GitHub Actions

#### 6.1 Add Packages Workflow (`.github/workflows/add-packages.yml`)

```yaml
name: Add Packages to Repository

on:
  workflow_dispatch:
    inputs:
      codename:
        description: 'Distribution codename (e.g., bookworm)'
        required: true
        type: string
      component:
        description: 'Repository component (e.g., jethome-tools)'
        required: true
        type: string
      artifact_name:
        description: 'Artifact name containing packages'
        required: false
        type: string
      packages_path:
        description: 'Path to packages directory'
        required: false
        type: string

jobs:
  add-packages:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repomanager
        uses: actions/checkout@v3

      - name: Download packages artifact
        if: ${{ inputs.artifact_name != '' }}
        uses: actions/download-artifact@v3
        with:
          name: ${{ inputs.artifact_name }}
          path: ./packages

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Import GPG key
        run: |
          echo "${{ secrets.GPG_PRIVATE_KEY }}" | base64 -d | gpg --batch --import
          gpg --list-secret-keys

      - name: Transfer packages to server
        run: |
          TEMP_DIR="/tmp/repomanager-$(date +%s)"
          rsync -avz ./packages/ ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}:$TEMP_DIR/

      - name: Add packages
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
            "debrepomanager add \
              --codename ${{ inputs.codename }} \
              --component ${{ inputs.component }} \
              --package-dir $TEMP_DIR"

      - name: Cleanup
        if: always()
        run: |
          gpg --batch --delete-secret-keys ${{ secrets.GPG_KEY_ID }}
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
            "rm -rf $TEMP_DIR"
```

---

## Порядок тестирования каждого модуля

1. **Config**: загрузка, мерж, доступ к параметрам
2. **Utils**: парсинг .deb, сравнение версий, поиск файлов
3. **Aptly** (с моками): создание repo, добавление пакетов, snapshots
4. **Retention**: группировка пакетов, применение политики
5. **GPG** (с моками): проверка ключа, импорт
6. **CLI**: парсинг аргументов, вызов функций (integration tests)

## Интеграционное тестирование

Создать полный workflow с тестовым aptly root:

```python
def test_full_workflow(tmp_path):
    # Setup test aptly root
    # Create test .deb files
    # Run full add workflow
    # Verify packages in repository
    # Run cleanup
    # Verify old packages removed
```

## Чеклист перед релизом

- [ ] Все тесты проходят
- [ ] Coverage > 80%
- [ ] Документация обновлена
- [ ] README с примерами использования
- [ ] GitHub Actions workflows протестированы
- [ ] Пример конфигурации актуален
- [ ] GPG signing работает
- [ ] Retention policy корректна

