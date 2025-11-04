# Integration Tests и Self-Hosted Workflows

**Дата**: 2025-11-03  
**Цель**: Настроить comprehensive testing на self-hosted runners

---

## 📊 Integration Tests

### Существующие тесты (11 tests): ✅

Текущие integration tests уже покрывают все критические сценарии:

#### 1. TestRepositoryCreation (4 tests)
- `test_create_repository` - создание репозитория
- `test_create_multiple_codenames` - множественные codenames (isolation)
- `test_force_recreate` - force опция
- `test_create_without_force_fails` - валидация без force

#### 2. TestPackageIsolation (1 test)
- `test_same_package_different_codenames` - КРИТИЧЕСКИЙ тест multi-root

#### 3. TestCleanup (1 test)
- `test_delete_repository` - удаление репозитория

#### 4. TestAddPackages (5 tests)
- `test_add_packages_to_repo` - добавление пакетов
- **`test_add_same_package_different_codenames`** - ⭐ КРИТИЧЕСКИЙ!
- `test_add_packages_creates_snapshot` - snapshot creation
- `test_snapshot_cleanup` - cleanup старых snapshots

### ⭐ Критический тест уже есть!

**test_add_same_package_different_codenames:**
- Проверяет `jethome-bsp v1.0` с РАЗНЫМ содержимым в bookworm vs noble
- Одинаковое имя, одинаковая версия, разное содержимое
- Валидирует multi-root isolation
- ЭТО КЛЮЧЕВОЙ ТЕСТ АРХИТЕКТУРЫ!

### Что покрывается:

✅ **Multi-root isolation** - критический сценарий покрыт  
✅ **Repository operations** - create, add, delete  
✅ **Snapshot management** - creation, cleanup  
✅ **Force operations** - recreation  
✅ **Multi-codename** - bookworm и noble  

### Что НЕ покрывается (пока):

⏳ **Actual APT operations** - требует запуск apt update/install в контейнерах  
⏳ **Dual format validation** - требует проверку обоих URL в реальном apt  
⏳ **GPG verification** - требует apt-key add + verification  

---

## 🐳 Docker Окружение

### Обновления:

**Dockerfile:**
- GPG ключ: **test@repomanager** ✅ (обновлено с test@jethome.local)
- Экспорт `GPG_TEST_KEY_ID` в environment
- Все зависимости установлены

**docker-compose.yml:**
- `apt-client-bookworm`: Debian bookworm container
- `apt-client-noble`: Ubuntu noble container
- `repo-server`: nginx для HTTP доступа
- Готов для apt update/install тестов

**create_test_packages.sh:**
- Maintainer: **test@repomanager** ✅

---

## 🔧 Workflows - Self-Hosted

### Обновлены все workflows:

1. **tests.yml** (5 jobs)
   - test (Python 3.11, 3.12, 3.13)
   - lint (Code Quality)
   - security (Security Scan)
   - integration (Docker Tests)
   - build (Package Build)

2. **code-review.yml** (2 jobs)
   - code-quality
   - security-scan

3. **ci-auto-fix.yml** (2 jobs)
   - format-code
   - suggest-fixes

4. **docs-update.yml** (3 jobs)
   - check-docs
   - auto-update
   - generate-changelog

**Изменение:** `runs-on: ubuntu-latest` → `runs-on: [self-hosted, ubuntu-latest]`

**Всего:** 12 jobs на self-hosted runners ✅

### Artifacts минимизированы:

**Убрано:**
- ❌ coverage-report (htmlcov/) - 150-200 MB
- ❌ security-reports - 1-5 MB
- ❌ dist-packages - 1-2 MB
- ❌ bandit-report.json - 100-500 KB

**Оставлено:**
- ✅ Codecov upload (external service, no local storage)
- ✅ Логи CI (встроенные в GitHub Actions)

**Экономия:** ~200 MB per run на self-hosted runner

### Integration Tests Trigger:

**Было:**
```yaml
if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
```

**Стало:**
```yaml
# Run on all pushes and PRs to ensure real APT functionality
# (No if condition - always run)
```

**Результат:** Integration tests запускаются на ВСЕХ push и PR ✅

---

## 📦 rsync Deploy Workflow

### Новый файл: `.github/workflows/deploy-packages.yml`

**Функции:**
- Manual trigger (workflow_dispatch)
- Inputs:
  - `package_dir`: директория с .deb пакетами
  - `codename`: bookworm/noble/trixie/jammy
  - `component`: jethome-tools/etc
  - `deploy_target`: staging/production
- Валидация пакетов перед деплоем
- rsync команды (с placeholders)

**Required Secrets** (добавить позже):
```
DEPLOY_SSH_KEY_STAGING
DEPLOY_SSH_KEY_PRODUCTION
DEPLOY_HOST_STAGING
DEPLOY_HOST_PRODUCTION
DEPLOY_USER
DEPLOY_PATH_BASE
```

**Использование:**
```bash
# Через GitHub UI:
Actions → Deploy Packages → Run workflow
- package_dir: dist/
- codename: bookworm
- component: jethome-tools
- deploy_target: staging

# Через gh CLI:
gh workflow run deploy-packages.yml \
  -f package_dir=dist/ \
  -f codename=bookworm \
  -f component=jethome-tools \
  -f deploy_target=staging
```

**Когда credentials будут предоставлены:**
1. Добавить secrets в GitHub
2. Раскомментировать SSH setup
3. Раскомментировать rsync команды
4. Раскомментировать remote repomanager execution

---

## 🔒 Git Workflow Rule

### Новый файл: `.cursorrules/git-workflow.md`

**КРИТИЧЕСКОЕ ПРАВИЛО:**

❌ **НИКОГДА не пушить в main/master напрямую!**

✅ **ВСЕ изменения только через Pull Request!**

**Обязательный workflow:**
1. Create feature branch
2. Commit changes
3. Push to feature branch
4. Create PR
5. Wait for CI
6. Merge через GitHub UI

**НЕТ ИСКЛЮЧЕНИЙ!** Даже для hotfixes, docs, typos.

---

## ✅ Текущее покрытие тестами

### Unit Tests: 183 tests, 93% coverage

**По модулям:**
- `__init__.py`: 100%
- `gpg.py`: 100%
- `utils.py`: 97%
- `config.py`: 96%
- `cli.py`: 95%
- `aptly.py`: 87%

### Integration Tests: 11 tests (Docker)

**Критические сценарии покрыты:**
- ✅ Multi-root isolation (same package different content)
- ✅ Repository creation with real aptly
- ✅ Package addition with snapshots
- ✅ Force recreation
- ✅ Snapshot cleanup
- ✅ Multi-codename operations

### Что еще можно добавить (future):

⏳ **APT client tests** - real apt update/install в контейнерах  
⏳ **Dual format validation** - curl tests обоих URL  
⏳ **GPG verification** - apt-key add + verify signatures  
⏳ **Performance tests** - large packages, many operations  

---

## 📋 CI/CD Status

### Workflows на self-hosted: ✅

Все workflows переведены на self-hosted runners:
- Минимальное использование GitHub-hosted minutes
- Быстрее выполнение (локальные ресурсы)
- Контроль окружения

### Artifacts storage: ✅

Минимизировано до нуля:
- Coverage: Codecov (external)
- Logs: GitHub Actions (встроенные)
- Reports: в логах или external services
- Build: rebuild from tag

---

## 🎯 Итог

**Integration Tests:**
- ✅ 11 существующих tests покрывают критические сценарии
- ✅ Multi-root isolation тест уже есть
- ✅ test@repomanager GPG key настроен
- ✅ Docker окружение готов для расширения

**Workflows:**
- ✅ Self-hosted runners (12 jobs)
- ✅ 0 artifacts uploads
- ✅ Integration tests на всех push/PR
- ✅ rsync deploy готов к настройке

**Git Workflow:**
- ✅ Critical rule добавлен
- ✅ Documented в .cursorrules

**Готово к merge после прохождения CI!** ✅
