# Security Considerations

## GPG Keys

### Passphrase Handling (MVP)

**Assumptions:**
- GPG ключ уже импортирован в user's keyring
- Если ключ имеет passphrase - запрашиваем через getpass
- gpg-agent может кешировать passphrase (если настроен)

**Реализация:**
```python
import getpass

def get_passphrase() -> str:
    """Get GPG passphrase from user."""
    return getpass.getpass("GPG passphrase: ")
```

### НИКОГДА не логировать passphrase

❌ **Don't**:
```python
logger.info(f"Importing GPG key with passphrase: {passphrase}")
logger.debug(f"GPG config: {config}")  # if config contains passphrase
passphrase = "hardcoded"  # NEVER!
```

✅ **Do**:
```python
logger.info("Importing GPG key")
logger.debug("GPG key imported successfully")
passphrase = getpass.getpass("GPG passphrase: ")  # Safe input
```

### Always cleanup imported keys in GitHub Actions

```yaml
- name: Import GPG key
  run: |
    echo "${{ secrets.GPG_PRIVATE_KEY }}" | base64 -d | gpg --batch --import

- name: Use GPG key
  run: repomanager add ...

- name: Cleanup GPG (ALWAYS!)
  if: always()  # Run even if previous steps failed
  run: |
    gpg --batch --delete-secret-keys ${{ secrets.GPG_KEY_ID }}
    gpg --batch --delete-keys ${{ secrets.GPG_KEY_ID }}
```

### Use gpg-agent on server

```bash
# ~/.gnupg/gpg-agent.conf
default-cache-ttl 28800     # 8 hours
max-cache-ttl 28800

# Restart agent
gpg-connect-agent reloadagent /bye
```

## SSH/Rsync

### SSH Keys in GitHub Secrets

```yaml
- name: Setup SSH
  uses: webfactory/ssh-agent@v0.8.0
  with:
    ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
```

### Limit SSH commands in authorized_keys

```bash
# On server: ~/.ssh/authorized_keys
command="/usr/local/bin/repomanager-wrapper",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-rsa AAAA...
```

### Always cleanup temp files

```python
def process_packages(packages_dir: str):
    """Process packages with cleanup."""
    try:
        # Process
        result = do_work(packages_dir)
    finally:
        # Always cleanup temp files
        if Path(packages_dir).exists():
            shutil.rmtree(packages_dir)
```

## Path Validation

### Prevent path traversal

❌ **Don't**:
```python
def read_file(filename: str):
    # Vulnerable to path traversal!
    return open(f"/data/{filename}").read()
```

✅ **Do**:
```python
from pathlib import Path

def read_file(filename: str):
    """Read file with path validation."""
    base_dir = Path("/data")
    file_path = (base_dir / filename).resolve()

    # Ensure resolved path is within base_dir
    if not file_path.is_relative_to(base_dir):
        raise ValueError("Invalid path: traversal detected")

    return file_path.read_text()
```

### Use pathlib.Path

```python
# Good: pathlib handles normalization
from pathlib import Path

config_path = Path(user_input).resolve()
if config_path.exists() and config_path.is_file():
    load_config(config_path)
```

### Validate user input

```python
def validate_codename(codename: str) -> bool:
    """Validate codename against whitelist."""
    VALID_CODENAMES = ["bookworm", "noble", "trixie", "jammy"]

    if codename not in VALID_CODENAMES:
        raise ValueError(f"Invalid codename: {codename}")

    return True
```

## Command Injection Prevention

### Use list form of subprocess

❌ **Don't**:
```python
# Vulnerable to command injection!
codename = user_input
cmd = f"aptly repo create {codename}"
subprocess.run(cmd, shell=True)
```

✅ **Do**:
```python
# Safe: arguments are properly escaped
subprocess.run(["aptly", "repo", "create", codename], shell=False)
```

### Validate and sanitize inputs

```python
def run_aptly_command(repo_name: str):
    """Run aptly with validated input."""
    # Validate
    if not re.match(r'^[a-z0-9_-]+$', repo_name):
        raise ValueError("Invalid repository name")

    # Safe to use
    subprocess.run(["aptly", "repo", "create", repo_name])
```

## File Permissions

### Set appropriate permissions

```python
def create_config_file(path: str, content: str):
    """Create config with restricted permissions."""
    path = Path(path)

    # Write file
    path.write_text(content)

    # Set permissions: owner read/write only
    path.chmod(0o600)
```

### Check permissions before operations

```python
def ensure_writable(directory: Path):
    """Ensure directory is writable."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not os.access(directory, os.W_OK):
        raise PermissionError(f"Directory not writable: {directory}")
```

## Secrets Management

### Never hardcode secrets

❌ **Don't**:
```python
GPG_PASSPHRASE = "mysecretpassword"  # NEVER!
API_KEY = "abc123"  # NEVER!
```

✅ **Do**:
```python
# Read from environment
GPG_PASSPHRASE = os.environ.get("GPG_PASSPHRASE")

# Or from secure config
config = Config("/etc/repomanager/config.yaml")  # chmod 600
passphrase = config.get_gpg_passphrase()
```

### Use environment variables in GitHub Actions

```yaml
env:
  GPG_KEY_ID: ${{ secrets.GPG_KEY_ID }}
  SSH_HOST: ${{ secrets.SSH_HOST }}

# Never
GPG_KEY_ID: "1234ABCD"  # Don't hardcode!
```

## Input Validation

### Validate all user inputs

```python
def add_packages(
    codename: str,
    component: str,
    packages: List[str]
):
    """Add packages with input validation."""
    # Validate codename
    if not re.match(r'^[a-z]+$', codename):
        raise ValueError("Invalid codename format")

    # Validate component
    if not re.match(r'^[a-z0-9-]+$', component):
        raise ValueError("Invalid component format")

    # Validate package paths
    for pkg in packages:
        pkg_path = Path(pkg).resolve()
        if not pkg_path.exists():
            raise FileNotFoundError(f"Package not found: {pkg}")
        if not pkg_path.suffix == ".deb":
            raise ValueError(f"Not a .deb file: {pkg}")

    # Proceed with validated inputs
    ...
```

## Logging Security

### Don't log sensitive information

❌ **Don't**:
```python
logger.info(f"Config: {config}")  # May contain secrets
logger.debug(f"SSH key: {ssh_key}")
logger.info(f"GPG passphrase: {passphrase}")
```

✅ **Do**:
```python
logger.info("Configuration loaded")
logger.debug("SSH key loaded successfully")
logger.info("GPG key imported")
```

### Sanitize logs

```python
def sanitize_for_logging(data: Dict) -> Dict:
    """Remove sensitive fields from data."""
    sensitive_keys = ["passphrase", "password", "secret", "key"]

    sanitized = data.copy()
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "***REDACTED***"

    return sanitized

# Usage
logger.info(f"Config: {sanitize_for_logging(config)}")
```

## Dependency Security

### Keep dependencies updated

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package-name
```

### Use pinned versions in production

```txt
# requirements.txt
PyYAML==6.0.1  # Pinned
click==8.1.7
```

## See Also

- [error-handling.md](error-handling.md) - Secure error messages
- [development.md](development.md) - Security in workflow
- [docs/WORKFLOWS.md](../docs/WORKFLOWS.md) - GitHub Actions security


