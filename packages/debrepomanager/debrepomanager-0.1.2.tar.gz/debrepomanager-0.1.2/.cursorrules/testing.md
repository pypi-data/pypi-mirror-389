# Testing Requirements

## 🎯 Core Principle

**ВСЕГДА добавлять тесты при написании нового кода!**

## Coverage Requirements

### Требования для MVP
- **Общее покрытие**: 80% minimum (цель: 85%+)
- **Критичные модули** (config, aptly): 85%+ обязательно
- **Другие модули** (gpg, utils, cli): 80%+
- **Новый код**: должен иметь тесты перед merge (TDD preferred)

### Проверка в CI
GitHub Actions автоматически проверяет coverage при каждом PR.
Минимальный порог: 80% (см. pyproject.toml)

### Проверка coverage
```bash
# Run tests with coverage
pytest --cov=repomanager --cov-report=term-missing

# Generate HTML report
pytest --cov=repomanager --cov-report=html
xdg-open htmlcov/index.html

# With make
make test-coverage
```

## Testing Framework

### Tools
- **pytest**: основной test runner
- **pytest-mock**: для мокирования
- **pytest-cov**: для coverage
- **unittest.mock**: для сложных моков

### Test File Location
```
tests/
├── __init__.py
├── test_config.py         # Tests for repomanager/config.py
├── test_aptly.py          # Tests for repomanager/aptly.py
├── test_retention.py      # Tests for repomanager/retention.py
├── test_gpg.py           # Tests for repomanager/gpg.py
├── test_utils.py         # Tests for repomanager/utils.py
└── test_cli.py           # Tests for repomanager/cli.py
```

**Convention**: `tests/test_<module_name>.py`

## Test Structure

### Basic Test
```python
import pytest
from repomanager.module import SomeClass


def test_basic_functionality():
    """Test basic functionality."""
    obj = SomeClass()
    result = obj.method()
    assert result == expected_value
```

### Test with Fixtures
```python
@pytest.fixture
def sample_config():
    """Provide sample configuration."""
    return {
        "aptly": {
            "root_base": "/tmp/test-aptly"
        }
    }


def test_with_fixture(sample_config):
    """Test using fixture."""
    config = Config(sample_config)
    assert config.aptly_root_base == "/tmp/test-aptly"
```

### Test with Mocks
```python
@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess calls."""
    return mocker.patch("subprocess.run")


def test_with_mock(mock_subprocess):
    """Test with mocked external calls."""
    from repomanager.aptly import AptlyManager

    manager = AptlyManager(config)
    manager.create_repo("bookworm", "main")

    # Verify subprocess was called correctly
    mock_subprocess.assert_called_once()
    args = mock_subprocess.call_args[0][0]
    assert "aptly" in args
    assert "repo" in args
    assert "create" in args
```

## Test Types

### Unit Tests
**Тестируют отдельные функции/методы в изоляции**

```python
def test_version_comparison():
    """Test Debian version comparison."""
    from repomanager.utils import compare_versions

    assert compare_versions("1.0", "2.0") < 0
    assert compare_versions("2.0", "1.0") > 0
    assert compare_versions("1.0", "1.0") == 0
```

**Markers**: `@pytest.mark.unit`

### Integration Tests
**Тестируют взаимодействие компонентов**

```python
@pytest.mark.integration
def test_full_add_workflow(tmp_path, mock_aptly):
    """Test full package addition workflow."""
    config = Config()
    manager = AptlyManager(config)

    # Create test package
    test_pkg = tmp_path / "test.deb"
    test_pkg.write_bytes(b"fake deb")

    # Add package
    result = manager.add_packages(
        "bookworm",
        "jethome-tools",
        [str(test_pkg)]
    )

    assert result is True
    # Verify snapshot was created
    # Verify published
```

**Markers**: `@pytest.mark.integration`

### Slow Tests
**Долгие тесты (маркируются для пропуска)**

```python
@pytest.mark.slow
def test_large_repository():
    """Test with large repository."""
    # Long-running test
    pass
```

**Run**: `pytest -m "not slow"` для быстрых тестов

## Mocking Guidelines

### External Commands (subprocess)
```python
def test_aptly_command(mocker):
    """Test aptly command execution."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(
        returncode=0,
        stdout="success",
        stderr=""
    )

    from repomanager.aptly import AptlyManager
    manager = AptlyManager(config)
    result = manager.create_repo("bookworm", "main")

    assert result is True
    mock_run.assert_called_once()
```

### File System Operations
```python
def test_config_loading(tmp_path, mocker):
    """Test configuration file loading."""
    # Use tmp_path for real files
    config_file = tmp_path / "config.yaml"
    config_file.write_text("aptly:\n  root_base: /test")

    # Or mock os.path.exists
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data="..."))
```

### GPG Operations
```python
def test_gpg_signing(mocker):
    """Test GPG signing."""
    mock_gpg = mocker.patch("subprocess.run")

    from repomanager.gpg import GPGManager
    manager = GPGManager(config)
    result = manager.check_key_available("KEY_ID")

    mock_gpg.assert_called_once()
```

## Parameterized Tests

### Multiple test cases
```python
@pytest.mark.parametrize("version1,version2,expected", [
    ("1.0", "2.0", -1),
    ("2.0", "1.0", 1),
    ("1.0", "1.0", 0),
    ("1.0-1", "1.0-2", -1),
])
def test_version_comparison(version1, version2, expected):
    """Test version comparison with multiple cases."""
    from repomanager.utils import compare_versions
    assert compare_versions(version1, version2) == expected
```

## Test Fixtures

### Common Fixtures

#### Sample Configuration
```python
@pytest.fixture
def sample_config():
    """Provide sample configuration."""
    return Config({
        "aptly": {"root_base": "/tmp/test"},
        "gpg": {"key_id": "TEST_KEY"},
        "retention": {
            "default": {"min_versions": 5, "max_age_days": 90}
        }
    })
```

#### Temporary Directory
```python
@pytest.fixture
def temp_aptly_root(tmp_path):
    """Create temporary aptly root."""
    root = tmp_path / "aptly"
    root.mkdir()
    return root
```

#### Mock Subprocess
```python
@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess.run."""
    return mocker.patch("subprocess.run")
```

## Test Organization

### Module Test File Structure
```python
"""Tests for repomanager.config module."""

import pytest
from repomanager.config import Config


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_load_default(self):
        """Test default config loading."""
        pass

    def test_load_from_file(self, tmp_path):
        """Test loading from file."""
        pass


class TestConfigMerging:
    """Tests for configuration merging."""

    def test_merge_simple(self):
        """Test simple merge."""
        pass


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_invalid_path(self):
        """Test invalid path handling."""
        pass
```

## Error Testing

### Test Expected Exceptions
```python
def test_invalid_codename():
    """Test error on invalid codename."""
    from repomanager.aptly import AptlyManager

    manager = AptlyManager(config)

    with pytest.raises(ValueError, match="Invalid codename"):
        manager.create_repo("invalid!", "main")
```

### Test Error Messages
```python
def test_error_message():
    """Test error message content."""
    with pytest.raises(ValueError) as exc_info:
        # code that raises
        pass

    assert "specific error text" in str(exc_info.value)
```

## Running Tests

### All tests
```bash
pytest
```

### Specific file
```bash
pytest tests/test_config.py
```

### Specific test
```bash
pytest tests/test_config.py::test_load_default
```

### With coverage
```bash
pytest --cov=repomanager --cov-report=term-missing
```

### With markers
```bash
# Only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration
```

### Verbose output
```bash
pytest -v
pytest -vv
```

### With prints
```bash
pytest -s
```

## Make Commands

```bash
make test              # Run all tests
make test-verbose      # Run with verbose output
make test-coverage     # Run with coverage report
```

## CI/CD

Tests автоматически запускаются в GitHub Actions:
- На каждый PR
- На push в main/develop
- Matrix: Python 3.8, 3.9, 3.10, 3.11, 3.12

См. [docs/WORKFLOWS.md](../docs/WORKFLOWS.md) для деталей.

## TDD (Test-Driven Development)

### Рекомендуемый workflow
1. **Написать failing test** сначала
2. **Реализовать minimal код** чтобы тест прошел
3. **Refactor** код сохраняя тесты зелеными
4. **Repeat**

### Example TDD Cycle
```python
# 1. Write failing test
def test_new_feature():
    """Test new feature."""
    result = new_function()
    assert result == expected

# 2. Implement minimal code
def new_function():
    return expected

# 3. Refactor and improve
def new_function():
    # Proper implementation
    pass
```

## Best Practices

1. ✅ **One assertion per test** (когда возможно)
2. ✅ **Test names describe what they test**
3. ✅ **Arrange-Act-Assert pattern**
4. ✅ **Mock external dependencies**
5. ✅ **Use fixtures for common setup**
6. ✅ **Test edge cases and errors**
7. ✅ **Keep tests independent**
8. ✅ **Fast tests (< 1s per test ideally)**

## Anti-Patterns

1. ❌ **No tests for new code**
2. ❌ **Tests that depend on external services**
3. ❌ **Tests that depend on execution order**
4. ❌ **Tests without assertions**
5. ❌ **Tests that test implementation details**
6. ❌ **Slow tests without @pytest.mark.slow**

## See Also

- [code-style.md](code-style.md) - Code style guidelines
- [development.md](development.md) - Development workflow
- [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) - Full development guide


