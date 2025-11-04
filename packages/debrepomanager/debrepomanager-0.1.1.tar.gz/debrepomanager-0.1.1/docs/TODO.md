# TODO List - Development Checklist

## ✅ Completed

### Infrastructure & Documentation
- [x] Create project structure
- [x] Setup Python package (setup.py, pyproject.toml)
- [x] Configure development tools (black, flake8, mypy, pytest)
- [x] Write comprehensive documentation
  - [x] README.md
  - [x] QUICKSTART.md
  - [x] PLAN.md
  - [x] ARCHITECTURE.md
  - [x] IMPLEMENTATION_STEPS.md
  - [x] CONFIG.md
  - [x] DEVELOPMENT.md
  - [x] PROJECT_STRUCTURE.md
  - [x] SUMMARY.md
- [x] Create configuration template (config.yaml.example)
- [x] Setup testing infrastructure
- [x] Add LICENSE (MIT)
- [x] Create Makefile with dev commands
- [x] Setup .gitignore

## ✅ Phase 1: Core Modules (COMPLETED)

### Config Module (`repomanager/config.py`)
- [x] Create Config class
- [x] Implement YAML loading
- [x] Implement config merging (repo + server)
- [x] Add validation
- [x] Property accessors for all config values
- [x] Method: `get_aptly_root(codename)`
- [x] Method: `get_retention_policy(component)`
- [x] **Tests**: `tests/test_config.py`
  - [x] Test default config loading
  - [x] Test YAML file loading
  - [x] Test config merging
  - [x] Test validation errors
  - [x] Test property accessors

### Utils Module (`repomanager/utils.py`)
- [x] Implement logging setup
- [x] Parse .deb metadata (python-debian)
- [x] Debian version comparison (apt_pkg)
- [x] Find .deb files in directory
- [x] PackageInfo dataclass
- [x] Get package age
- [x] **Tests**: `tests/test_utils.py`
  - [x] Test logging configuration
  - [x] Test .deb parsing
  - [x] Test version comparison
  - [x] Test file finding

### Aptly Wrapper (`repomanager/aptly.py`)
- [x] Create AptlyManager class
- [x] Method: `_run_aptly()` - execute aptly commands
- [x] Method: `_get_repo_name()` - internal naming
- [x] Method: `create_repo()` - create local repo
- [x] Method: `repo_exists()` - check if repo exists
- [x] Method: `add_packages()` - add packages to repo
- [x] Method: `create_snapshot()` - create snapshot from repo
- [x] Method: `publish_snapshot()` - publish/switch snapshot
- [x] Method: `list_packages()` - list packages in repo
- [x] Method: `remove_packages()` - remove packages
- [x] Method: `cleanup_snapshots()` - remove old snapshots
- [x] Method: `delete_repo()` - delete repo and snapshots
- [x] **Tests**: `tests/test_aptly.py`
  - [x] Mock subprocess.run
  - [x] Test create_repo
  - [x] Test add_packages
  - [x] Test snapshot creation
  - [x] Test publish/switch
  - [x] Test list operations
  - [x] Test cleanup

## ✅ Phase 2: CLI Basic (COMPLETED)

### CLI Core (`repomanager/cli.py`)
- [x] Setup click/argparse structure
- [x] Main entry point
- [x] Global options: --config, --verbose, --dry-run
- [x] Command routing
- [x] Error handling
- [x] Exit codes
- [x] **Tests**: `tests/test_cli.py`
  - [x] Test argument parsing
  - [x] Test global options
  - [x] Test error handling

### Add Command
- [x] Implement `add` command
- [x] Parse arguments (codename, component, packages/package-dir)
- [x] Scan directory for .deb files
- [x] Check/create repository (if auto_create)
- [x] Add packages via aptly
- [x] Create snapshot
- [x] Publish/switch atomically
- [x] Cleanup old snapshots
- [x] Progress output
- [x] **Tests**: Integration test with mocked aptly

### Repository Management Commands
- [x] Implement `create-repo` command
- [x] Implement `delete-repo` command (with confirmation)
- [x] Implement `list` command
  - [x] List all repos
  - [x] List repos for codename
  - [x] List packages in component
- [x] Implement `verify` command
  - [x] Check repo consistency
  - [x] Verify GPG signatures
- [x] **Tests**: Integration tests

## ✅ Phase 3: GPG Integration (COMPLETED)

### GPG Integration (`repomanager/gpg.py`)
- [x] Create GPGManager class
- [x] Method: `check_key_available()` - check key in keyring
- [x] Method: `test_signing()` - test signing capability
- [x] Method: `configure_for_aptly()` - return aptly signing config
- [x] **Tests**: `tests/test_gpg.py`
  - [x] Mock GPG operations
  - [x] Test key checking
  - [x] Test signing

### Retention Policy (`repomanager/retention.py`) - **DEFERRED to Phase 8**
- [ ] Create RetentionPolicy dataclass
- [ ] Function: `group_packages_by_name()`
- [ ] Method: `get_packages_to_remove()`
  - [ ] Group by name
  - [ ] Sort by version
  - [ ] Keep min_versions
  - [ ] Remove old beyond min_versions
- [ ] **Tests**: `tests/test_retention.py`
  - [ ] Test grouping
  - [ ] Test policy application
  - [ ] Test edge cases (few packages, all new, all old)

### Cleanup Command - **DEFERRED to Phase 8**
- [ ] Implement `cleanup` command
- [ ] Parse arguments (codename, component, --dry-run, --apply)
- [ ] Get packages from aptly
- [ ] Apply retention policy
- [ ] Remove packages
- [ ] Create new snapshot
- [ ] Publish atomically
- [ ] Generate report
- [ ] **Tests**: Integration test with mocked aptly

## ✅ Phase 4: Dual Format Support (COMPLETED)

### Symlink Management
- [x] Implement `_create_dual_format_symlinks()` in `aptly.py`
- [x] Integrate symlink creation in `_publish_snapshot()`
- [x] Support for both old and new URL formats
- [x] Configurable via `dual_format.enabled` and `dual_format.auto_symlink`
- [x] **Tests**: `tests/test_aptly.py::TestDualFormatSupport`
  - [x] Test symlink creation
  - [x] Test symlink update
  - [x] Test relative paths
  - [x] Test integration with publish
  - [x] Test configuration flags

## 🔨 Phase 5: GitHub Actions (DEFERRED to v1.1)

### Add Packages Workflow (`.github/workflows/add-packages.yml`)
- [ ] Create workflow file
- [ ] Define inputs (codename, component, artifact_name, packages_path)
- [ ] Checkout repomanager
- [ ] Download artifacts
- [ ] Setup SSH (webfactory/ssh-agent)
- [ ] Import GPG key
- [ ] rsync packages to server
- [ ] SSH execute debrepomanager add
- [ ] Cleanup (always block)
- [ ] Report summary

### Cleanup Workflow (`.github/workflows/cleanup-repo.yml`)
- [ ] Create workflow file
- [ ] Schedule trigger (weekly)
- [ ] Manual trigger (workflow_dispatch)
- [ ] Setup SSH
- [ ] SSH execute repomanager cleanup
- [ ] Collect and post report

### Create Repo Workflow (`.github/workflows/create-repo.yml`)
- [ ] Create workflow file
- [ ] Manual trigger (workflow_dispatch)
- [ ] Define inputs (codename, component)
- [ ] Setup SSH and GPG
- [ ] SSH execute debrepomanager create-repo
- [ ] Verify creation

### CI/CD Testing Workflow (`.github/workflows/tests.yml`)
- [ ] Create workflow file
- [ ] Run on push/PR
- [ ] Matrix: Python 3.8, 3.9, 3.10, 3.11
- [ ] Run tests with coverage
- [ ] Upload coverage to codecov
- [ ] Run linters (black, flake8, mypy)

## 🔨 Phase 5: Testing & Polish

### Unit Tests
- [ ] Achieve 80%+ code coverage
- [ ] Critical modules (config, aptly, retention) 90%+
- [ ] All tests passing
- [ ] No skipped tests

### Integration Tests
- [ ] Full workflow test (add packages end-to-end)
- [ ] Cleanup workflow test
- [ ] Multi-codename test
- [ ] Error handling tests

### Documentation Updates
- [ ] Update README with real examples
- [ ] Add screenshots/demos (optional)
- [ ] Update CHANGELOG for v0.1.0
- [ ] Create WORKFLOWS.md with GitHub Actions details
- [ ] Review all docs for accuracy

### Code Quality
- [ ] All code formatted with black
- [ ] No flake8 violations
- [ ] No mypy errors
- [ ] Docstrings for all public functions
- [ ] Type hints on all functions

## 🚀 Release Preparation

### Pre-release Checklist
- [ ] All tests passing
- [ ] Coverage > 80%
- [ ] Documentation complete
- [ ] CHANGELOG updated
- [ ] Version bumped in __init__.py and setup.py
- [ ] GitHub Actions tested
- [ ] GPG signing tested
- [ ] README examples verified

### Release v0.1.0
- [ ] Create git tag v0.1.0
- [ ] Push to GitHub
- [ ] Create GitHub Release
- [ ] Upload to PyPI (optional)
- [ ] Announce release

## 📝 Future Enhancements (Post v0.1.0)

### Security & Operations
- [ ] **GPG Key Rotation** (v1.1 - высокий приоритет)
  - [ ] Command: `debrepomanager rotate-gpg-key --new-key-id <ID>`
  - [ ] Переподпись всех репозиториев новым ключом
  - [ ] Экспорт нового публичного ключа
  - [ ] Генерация миграционного скрипта для клиентов
  - [ ] Поддержка grace period (оба ключа валидны)
  - [ ] Валидация успешной ротации
  - [ ] Уведомления для администраторов
  - [ ] Rollback mechanism при ошибках
  - [ ] Документация процесса ротации
  - [ ] Automated tests для ротации
  - [ ] Поддержка ротации без downtime

### Features
- [ ] REST API server (Flask/FastAPI)
- [ ] Web UI for repository management
- [ ] Monitoring/metrics (Prometheus)
- [ ] Multi-server support (rsync mirrors)
- [ ] Database for metadata (instead of aptly db)
- [ ] Advanced retention policies (based on downloads, importance)
- [ ] Package vulnerability scanning
- [ ] Automated changelog generation

### Improvements
- [ ] Parallel operations support
- [ ] Incremental updates optimization
- [ ] Better error messages
- [ ] Progress bars (rich/tqdm)
- [ ] Shell completion (click-completion)
- [ ] Docker image
- [ ] Ansible playbook for deployment

## 📌 Notes

- Prioritize MVP (critical path) first
- Write tests alongside code (TDD)
- Keep commits atomic and well-described
- Update documentation as you go
- Test in real environment before release

---

**Track your progress by checking off items as you complete them!**

