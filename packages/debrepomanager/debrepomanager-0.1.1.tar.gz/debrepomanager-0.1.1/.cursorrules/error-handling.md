# Error Handling Patterns

## Always Handle These Exceptions

- `subprocess.CalledProcessError` - aptly, gpg commands
- `FileNotFoundError` - config files, packages
- `PermissionError` - aptly roots, publish directories
- `yaml.YAMLError` - config parsing

## Exception Hierarchy

```python
class RepomanagerError(Exception):
    """Base exception for all repomanager errors."""

class ConfigError(RepomanagerError):
    """Configuration related errors."""

class AptlyError(RepomanagerError):
    """Aptly operation errors."""

class GPGError(RepomanagerError):
    """GPG operation errors."""

class RetentionError(RepomanagerError):
    """Retention policy errors."""
```

## Pattern: Wrap and Re-raise

```python
try:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e}")
    logger.debug(f"Stderr: {e.stderr}")
    raise AptlyError(f"Aptly operation failed: {e.stderr}") from e
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise ConfigError(f"Config file not found: {e}") from e
```

## Pattern: Catch-Log-Raise

```python
def critical_operation():
    """Operation that must succeed."""
    try:
        # Operation
        result = do_something()
    except Exception as e:
        logger.error(f"Critical operation failed: {e}", exc_info=True)
        raise
```

## Pattern: Try-Finally for Cleanup

```python
def with_temp_files():
    """Ensure cleanup even on error."""
    temp_files = []
    try:
        temp_file = create_temp()
        temp_files.append(temp_file)
        # Process
        process(temp_file)
    finally:
        # Cleanup always runs
        for f in temp_files:
            if f.exists():
                f.unlink()
```

## Pattern: Context Manager

```python
from contextlib import contextmanager

@contextmanager
def temporary_repo(manager, codename, component):
    """Context manager for temporary repository."""
    try:
        manager.create_repo(codename, component)
        yield
    finally:
        manager.delete_repo(codename, component)

# Usage
with temporary_repo(manager, "test", "temp") as repo:
    manager.add_packages(...)
# Auto-cleanup
```

## Subprocess Error Handling

```python
def run_command(cmd: List[str]) -> str:
    """Run command with proper error handling."""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {' '.join(cmd)}")
        raise RuntimeError("Command timed out")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Command failed: {e.stderr}") from e
```

## File Operations Error Handling

```python
def load_config(path: str) -> Dict[str, Any]:
    """Load config with error handling."""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        raise ConfigError(f"Config file not found: {path}")
    except PermissionError:
        logger.error(f"Permission denied: {path}")
        raise ConfigError(f"Cannot read config: permission denied")
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {path}: {e}")
        raise ConfigError(f"Invalid YAML syntax: {e}")
```

## Validation with Early Returns

```python
def validate_and_process(codename: str, packages: List[str]):
    """Validate inputs before processing."""
    # Early validation
    if not codename:
        raise ValueError("Codename cannot be empty")

    if codename not in VALID_CODENAMES:
        raise ValueError(f"Invalid codename: {codename}")

    if not packages:
        raise ValueError("No packages provided")

    for pkg in packages:
        if not Path(pkg).exists():
            raise FileNotFoundError(f"Package not found: {pkg}")

    # Process only if validation passed
    return process_packages(codename, packages)
```

## Retry Pattern

```python
from time import sleep

def retry_operation(
    operation,
    max_retries: int = 3,
    delay: float = 1.0
):
    """Retry operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts")
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
            sleep(delay * (2 ** attempt))
```

## Logging Best Practices

```python
# Log at different levels
logger.debug("Detailed debug info")
logger.info("Normal operation")
logger.warning("Something unexpected but handled")
logger.error("Error occurred", exc_info=True)  # Include traceback

# Include context
logger.error(f"Failed to process {package}: {error}")

# Don't log sensitive info
logger.info(f"GPG key imported")  # Good
logger.info(f"GPG passphrase: {passphrase}")  # BAD!!!
```

## CLI Error Handling

```python
@click.command()
def command():
    """Command with proper error handling."""
    try:
        result = do_operation()
        click.echo("Success!")
    except ConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except AptlyError as e:
        click.echo(f"Aptly error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        logger.exception("Unexpected error")
        sys.exit(99)
```

## Exit Codes

```python
# Define exit codes
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_APTLY_ERROR = 2
EXIT_GPG_ERROR = 3
EXIT_PERMISSION_ERROR = 4
EXIT_UNEXPECTED_ERROR = 99
```

## See Also

- [architecture.md](architecture.md) - Error hierarchy
- [security.md](security.md) - Security in error messages
- [code-style.md](code-style.md) - Logging guidelines


