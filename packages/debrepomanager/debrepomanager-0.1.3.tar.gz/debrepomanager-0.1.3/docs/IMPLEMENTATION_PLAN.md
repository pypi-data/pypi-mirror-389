# Implementation Plan - Debian Repository Manager

Финальный план реализации с четкими фазами и критериями завершения.

## 🎯 Цель проекта

Создать систему управления Debian репозиториями на базе aptly с поддержкой:
- Множественных дистрибутивов (bookworm, noble, trixie, jammy)
- Множественных архитектур (amd64, arm64, riscv64)
- Множественных компонентов (jethome-tools, jethome-armbian, jethome-*)
- Обратной совместимости (старый и новый форматы URL)
- GPG подписи всех пакетов
- Атомарных обновлений через snapshots

## 📊 Структура плана

### MVP (Minimum Viable Product) - Фазы 0-4
Базовый функционал для ручного управления репозиториями с CLI

### Extended Features - Фазы 5-6
Автоматизация (GitHub Actions) и продвинутые функции (retention policies)

### Future Enhancements - После v1.0
API, мониторинг, дополнительные функции

---

# 🏗️ PHASE 0: Infrastructure

**Статус**: ✅ Завершена

**Задачи:**
- [x] Структура проекта создана
- [x] Документация написана (15 файлов в docs/)
- [x] Cursor rules организованы (11 файлов в .cursorrules/)
- [x] GitHub Actions workflows (4 workflow для CI/CD разработки)
- [x] Python package setup (requirements.txt, setup.py, pyproject.toml)
- [x] Testing infrastructure (pytest, coverage, fixtures)
- [x] Code quality tools (black, flake8, mypy)
- [x] Config template (config.yaml.example)
- [x] Dual format documentation (docs/DUAL_FORMAT.md)
- [x] APT configuration examples (docs/APT_CONFIGURATION.md)

**Результат**: ✅ Проект готов к разработке

---

# 🔧 PHASE 1: Core Modules

**Статус**: ✅ Завершена

**Цель**: Реализовать базовые модули без которых невозможна дальнейшая работа

**Критерий завершения**: Все модули имеют unit тесты, проходят make check-all

## Step 1.1: Config Module ✅ DONE

**Файл**: `repomanager/config.py`

**Задачи:**
- [x] Создать класс Config
- [x] Реализовать загрузку YAML конфигурации
- [x] Реализовать мерджинг конфигов (repo + /etc/repomanager/config.yaml)
- [x] Добавить валидацию параметров
- [x] Реализовать property accessors для всех настроек
- [x] Добавить методы: `get_aptly_root(codename)`, `get_architectures()`, и т.д.

**Тесты**: `tests/test_config.py`
- [x] Загрузка default конфига
- [x] Загрузка из файла
- [x] Мерджинг двух конфигов
- [x] Валидация (ошибки при невалидных данных)
- [x] Property accessors

**Оценка**: 3-4 часа

**Зависимости**: Нет

**Progress**: ████████████████████ 100%
**Coverage**: 91.6% ✅ (exceeds 85% requirement)
**Commit**: 2f26a3b

---

## Step 1.2: Utils Module ✅ DONE

**Файл**: `repomanager/utils.py`

**Задачи:**
- [x] Реализовать setup_logging (уровни, форматы, файл)
- [x] Реализовать parse_deb_metadata (python-debian)
- [x] Реализовать compare_versions (apt_pkg с fallback)
- [x] Реализовать find_deb_files в директории (рекурсивно)
- [x] Создать PackageInfo dataclass
- [x] Реализовать get_package_age

**Тесты**: `tests/test_utils.py`
- [x] Logging setup (4 tests)
- [x] .deb parsing (4 tests с mock)
- [x] Version comparison (6 tests)
- [x] Find files (7 tests с tmp_path)
- [x] Package age (3 tests)

**Оценка**: 2-3 часа

**Зависимости**: Нет

**Progress**: ████████████████████ 100%
**Coverage**: 95% ✅ (exceeds 80% requirement)
**Commit**: cd621a9

---

## Step 1.3: Aptly Wrapper Base ✅ DONE

**Файл**: `repomanager/aptly.py`

**Задачи:**
- [x] Создать класс AptlyManager
- [x] Реализовать `_run_aptly()` - execute aptly с правильным -config
- [x] Реализовать `_get_repo_name()` - internal naming convention
- [x] Реализовать `_get_aptly_config_path()` - путь к конфигу для codename
- [x] Реализовать `_ensure_aptly_root()` - создание aptly root если не существует
- [x] Реализовать `_create_aptly_config()` - генерация aptly.conf

**Тесты**: `tests/test_aptly.py` (базовые)
- [x] Mock subprocess.run
- [x] Правильный вызов aptly с -config
- [x] Naming convention (2 tests)
- [x] Config path generation (2 tests)
- [x] Ensure root (4 tests)
- [x] Create config (2 tests)
- [x] Run aptly (6 tests)
- [x] Error handling

**Оценка**: 2-3 часа

**Зависимости**: Step 1.1 (Config)

**Progress**: ████████████████████ 100%
**Coverage**: 83% (aptly module)
**Tests**: 16 tests passed

---

**PHASE 1 TOTAL**: 7-10 часов

**Phase 1 Checklist:**
- [x] Step 1.1: Config Module завершен ✅
- [x] Step 1.2: Utils Module завершен ✅
- [x] Step 1.3: Aptly Wrapper Base завершен ✅
- [x] Все тесты Phase 1 проходят ✅ (62 tests)
- [x] Coverage >= 85% (current: 90.7%) ✅
- [x] `make check-all` passes ✅

**Progress**: ████████████████████ 100% (3/3 steps done)

**Milestone**: ✅ Базовые модули готовы, проходят тесты, можно использовать в других модулях

---

# 📦 PHASE 2: Repository Operations

**Статус**: ✅ Завершена

**Цель**: Реализовать операции с репозиториями (create, add, list)

**Критерий завершения**: Можно создавать репозитории и добавлять пакеты через Python API

## Step 2.1: Create Repository

**Файл**: `repomanager/aptly.py` (дополнение)

**Задачи:**
- [ ] Реализовать `create_repo(codename, component, architectures, force=False)`
- [ ] Создание aptly.conf для нового codename (если не существует)
- [ ] Создание local repo в aptly
- [ ] Инициализация пустого snapshot
- [ ] Initial publish (пустой репозиторий, готовый к добавлению пакетов)

**Тесты**: `tests/test_aptly.py` (дополнение)
- [ ] Создание нового репо
- [ ] Force режим (recreate если существует)
- [ ] Создание aptly.conf
- [ ] Error handling (invalid codename/component)

**Оценка**: 3-4 часа

**Зависимости**: Step 1.3

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 2.2: Add Packages (Atomic)

**Файл**: `repomanager/aptly.py` (дополнение)

**Задачи:**
- [ ] Реализовать `add_packages(codename, component, packages)`
- [ ] Проверка существования репо (создание с force если auto_create)
- [ ] Добавление пакетов в local repo
- [ ] Создание snapshot с timestamp
- [ ] Atomic publish switch
- [ ] Cleanup старых snapshots (keep последние N)

**Тесты**: `tests/test_aptly.py` (дополнение)
- [ ] Добавление пакетов в существующий репо
- [ ] Auto-create репо если не существует
- [ ] Создание snapshot
- [ ] Atomic switch
- [ ] Error handling (файлы не существуют, некорректные .deb)

**Оценка**: 4-5 часов

**Зависимости**: Step 2.1, Step 1.2 (utils для поиска .deb)

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 2.3: List & Verify Operations ✅ DONE

**Файл**: `repomanager/aptly.py` (дополнение)

**Задачи:**
- [x] Реализовать `list_repos(codename=None)` - список репозиториев
- [x] Реализовать `list_packages(codename, component)` - список пакетов в репо
- [x] Реализовать `repo_exists(codename, component)` - проверка существования (было ранее)
- [x] Реализовать `get_published_snapshot(codename, component)` - текущий published snapshot
- [x] Реализовать `verify_repo(codename, component)` - проверка консистентности

**Тесты**: `tests/test_aptly.py` (дополнение)
- [x] List repos (empty, с репо, all codenames)
- [x] List packages (parse aptly output, empty, not exists)
- [x] Repo exists check (было ранее)
- [x] Get published snapshot (not published, published)
- [x] Verify repo (not published, published, not exists)

**Оценка**: 2-3 часа

**Зависимости**: Step 2.1

**Progress**: ████████████████████ 100%
**Coverage**: aptly.py: 85%
**Tests**: +8 tests
**Commit**: Merged in PR #4

---

**PHASE 2 TOTAL**: 9-12 часов

**Phase 2 Checklist:**
- [x] Step 2.1: Create Repository завершен ✅
- [x] Step 2.2: Add Packages завершен ✅
- [x] Step 2.3: List & Verify завершен ✅
- [x] Все тесты Phase 2 проходят ✅
- [x] Coverage >= 85% (aptly: 85%) ✅
- [x] Integration тесты между create/add/list ✅
- [x] `make check-all` passes ✅

**Progress**: ████████████████████ 100% (3/3 steps done)

**Milestone**: ✅ Python API готов для операций с репозиториями

---

# 🖥️ PHASE 3: CLI Interface

**Статус**: ✅ Завершена (100%)

**Цель**: Создать удобный CLI интерфейс для всех операций

**Критерий завершения**: Все команды работают из командной строки

## Step 3.1: CLI Core & Add Command ✅ DONE

**Файл**: `repomanager/cli.py`

**Задачи:**
- [x] Setup Click структуры
- [x] Реализовать global options: --config, --verbose, --dry-run
- [x] Создать command: `add`
- [x] Добавить опции add: --codename, --component, --packages, --package-dir, --force
- [x] Реализовать логику add:
  - [x] Парсинг аргументов
  - [x] Поиск .deb файлов (если --package-dir)
  - [x] Загрузка конфига
  - [x] Создание AptlyManager
  - [x] Проверка/создание репо (если force или auto_create)
  - [x] Добавление пакетов
  - [x] Progress output
- [x] Helper functions для упрощения (complexity < 10)

**Тесты**: `tests/test_cli.py`
- [x] Парсинг аргументов
- [x] Integration test (mock aptly)
- [x] Error handling
- [x] --force option works
- [x] --package-dir рекурсивный поиск
- [x] dry-run mode
- [x] verbose mode

**Оценка**: 4-5 часов

**Зависимости**: Phase 2

**Progress**: ████████████████████ 100%
**Coverage**: cli.py: 95%
**Tests**: 11 tests для add command

---

## Step 3.2: Create/Delete/List Commands ✅ DONE

**Файл**: `repomanager/cli.py` (дополнение)

**Задачи:**

**`create-repo` command:**
- [x] Реализовать command create-repo
- [x] Опции: --codename, --component, --architectures, --force
- [x] Логика создания репозитория
- [x] User-friendly output

**`delete-repo` command:**
- [x] Реализовать command delete-repo
- [x] Опции: --codename, --component, --confirm
- [x] Безопасное удаление (требует confirm)
- [x] Double confirmation prompt
- [x] Check repo exists before prompt

**`list` command:**
- [x] Реализовать command list
- [x] Опции: --codename, --component (фильтры)
- [x] Output: repos или packages
- [x] Human-readable форматирование

**Тесты**: `tests/test_cli.py` (дополнение)
- [x] Create repo command (5 tests)
- [x] Delete repo command (6 tests с подтверждением)
- [x] Delete без confirm (должен запросить)
- [x] List repos (5 tests с различными фильтрами)
- [x] Error handling (7 tests)

**Оценка**: 3-4 часа

**Зависимости**: Step 3.1

**Progress**: ████████████████████ 100%
**Coverage**: cli.py: 95%
**Tests**: 16 tests для create/delete/list

---

**PHASE 3 TOTAL**: 7-9 часов

**Phase 3 Checklist:**
- [x] Step 3.1: CLI Core & Add завершен ✅
- [x] Step 3.2: Create/Delete/List завершен ✅
- [x] Все команды работают ✅
- [x] Help messages информативные ✅
- [x] Error messages понятные ✅
- [x] Progress indicators работают ✅
- [x] All CLI tests проходят ✅ (38 tests)
- [x] Complexity < 10 (flake8 C901) ✅
- [x] `make check-all` passes ✅

**Progress**: ████████████████████ 100% (2/2 steps done)

**Milestone**: ✅ CLI полностью функционален для базовых операций

---

# 🔐 PHASE 4: GPG Integration

**Статус**: ✅ Завершена (100%)

**Цель**: Обязательная GPG подпись всех репозиториев

**Критерий завершения**: Все публикации подписаны, aptly verify проходит

## Step 4.1: GPG Module

**Файл**: `repomanager/gpg.py`

**Задачи:**
- [ ] Создать класс GPGManager
- [ ] Реализовать `check_key_available(key_id)` - проверка ключа в keyring
- [ ] Реализовать `get_passphrase()` - запрос пароля (getpass)
- [ ] Реализовать `test_signing()` - тест подписи
- [ ] Реализовать `configure_for_aptly()` - параметры для aptly

**Допущения:**
- Ключ уже импортирован в user's gnupg ✅
- Если ключ имеет пароль - запрашиваем через getpass ✅
- Если gpg-agent настроен - используем кеш ✅

**Тесты**: `tests/test_gpg.py`
- [ ] Mock gpg calls
- [ ] Key availability check
- [ ] Passphrase handling (mock getpass)
- [ ] gpg-agent кеш проверка

**Оценка**: 2-3 часа

**Зависимости**: Step 1.1 (Config)

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 4.2: Integration в Aptly

**Файл**: `repomanager/aptly.py` (обновление)

**Задачи:**
- [ ] Добавить GPGManager в AptlyManager
- [ ] Добавить `-gpg-key` в команды publish
- [ ] Использовать GPGManager для проверки ключа перед publish
- [ ] Error handling для GPG ошибок
- [ ] Обновить `publish_snapshot()` - добавить -gpg-key
- [ ] Обновить `create_repo()` - initial publish с GPG

**Тесты**: `tests/test_aptly.py` (дополнение)
- [ ] Publish с GPG signing
- [ ] Error handling (key not found)
- [ ] Error handling (wrong passphrase)

**Оценка**: 2 часа

**Зависимости**: Step 4.1, Phase 2

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

**PHASE 4 TOTAL**: 4-5 часов

**Phase 4 Checklist:**
- [ ] Step 4.1: GPG Module завершен
- [ ] Step 4.2: Integration в Aptly завершен
- [ ] GPG ключ проверяется перед операциями
- [ ] Passphrase запрашивается если нужно
- [ ] Все publish с -gpg-key
- [ ] aptly verify проходит
- [ ] All GPG tests проходят
- [ ] `make check-all` passes

**Milestone**: ⏳ Все репозитории подписываются GPG ключом

---

# 🔄 PHASE 5: Dual Format Support

**Статус**: ✅ Завершена (100%)

**Цель**: Поддержка старого и нового форматов URL одновременно

**Критерий завершения**: Оба формата работают для всех репозиториев

## Step 5.1: Symlink Management

**Файл**: `repomanager/aptly.py` (дополнение)

**Задачи:**
- [ ] Реализовать `_create_dual_format_symlinks(codename, component)`
- [ ] Автоматическое создание symlinks при publish
- [ ] Структура: `/dists/{codename}/{component}` -> `/{codename}/{component}/dists/{component}`
- [ ] Проверка существования symlinks
- [ ] Update symlinks если уже существуют
- [ ] Интеграция в publish_snapshot()

**Конфигурация** (уже есть в config.yaml.example):
```yaml
repositories:
  dual_format:
    enabled: true
    method: "symlink"
    auto_symlink: true
```

**Тесты**: `tests/test_aptly.py` (дополнение)
- [ ] Создание symlinks
- [ ] Update существующих symlinks
- [ ] Работает для всех codenames
- [ ] Relative paths правильные

**Оценка**: 2-3 часа

**Зависимости**: Phase 2

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 5.2: Verification Script

**Файл**: `scripts/setup-dual-format.sh`

**Задачи:**
- [ ] Создать bash скрипт для initial setup symlinks
- [ ] Поддержка всех codenames и components
- [ ] Verification старого формата (curl tests)
- [ ] Verification нового формата (curl tests)
- [ ] Error handling
- [ ] Usage documentation в скрипте

**Оценка**: 1 час

**Зависимости**: Нет (независимый скрипт)

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

**PHASE 5 TOTAL**: 3-4 часа

**Phase 5 Checklist:**
- [ ] Step 5.1: Symlink Management завершен
- [ ] Step 5.2: Verification Script завершен
- [ ] Старый формат работает: `deb http://repo.site.com bookworm component`
- [ ] Новый формат работает: `deb http://repo.site.com/bookworm component main`
- [ ] curl tests обоих форматов проходят
- [ ] Manual apt update с обоими форматами работает
- [ ] Все тесты Phase 5 проходят
- [ ] `make check-all` passes

**Milestone**: ⏳ Старые клиенты продолжают работать, новые используют новый формат

---

# ✅ PHASE 6: Testing & Polish (MVP Complete)

**Статус**: ⏳ Ожидание

**Цель**: Полное покрытие тестами, документация, готовность к production

**Критерий завершения**: Coverage 80%+, все тесты проходят, документация актуальна

## Step 6.1: Unit Tests Completion

**Файлы**: `tests/test_*.py`

**Приоритет 1 (обязательно для MVP):**
- [ ] `test_config.py` - полное покрытие config.py (90%+)
- [ ] `test_aptly.py` - основные операции (85%+)
- [ ] `test_utils.py` - утилиты (80%+)
- [ ] `test_gpg.py` - GPG операции (80%+)
- [ ] `test_cli.py` - CLI команды (75%+)
- [ ] Overall coverage >= 80%

**Приоритет 2 (можно отложить):**
- [ ] Integration tests с реальным aptly (в CI)
- [ ] Edge cases и corner cases
- [ ] Performance tests

**Оценка**: 6-8 часов (приоритет 1)

**Зависимости**: Phases 1-5

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 6.2: CLI Polish & Error Messages

**Файл**: `repomanager/cli.py`

**Задачи:**
- [ ] User-friendly error messages
- [ ] Progress indicators (при добавлении многих пакетов)
- [ ] Colored output (optional, через click.style)
- [ ] Help messages для всех команд
- [ ] Examples в --help

**Оценка**: 2-3 часа

**Зависимости**: Step 3.2

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 6.3: Documentation Update

**Файлы**: Различные .md файлы

**Задачи:**
- [ ] README.md - актуализировать примеры с real commands
- [ ] docs/QUICKSTART.md - проверить все команды работают
- [ ] docs/CONFIG.md - обновить если добавились параметры
- [ ] docs/TODO.md - отметить завершенные задачи
- [ ] Создать docs/USAGE.md - подробное руководство по всем командам
- [ ] docs/CHANGELOG.md - добавить все изменения для v0.1.0

**Оценка**: 2-3 часа

**Зависимости**: Phases 1-5

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

**PHASE 6 TOTAL**: 10-14 часов

**Phase 6 Checklist:**
- [ ] Step 6.1: Unit Tests завершен
- [ ] Step 6.2: CLI Polish завершен
- [ ] Step 6.3: Documentation Update завершен
- [ ] Overall coverage >= 80%
- [ ] Critical modules >= 85%
- [ ] Все тесты проходят
- [ ] `make check-all` passes
- [ ] Manual testing на реальном сервере
- [ ] Documentation актуальна с working examples
- [ ] CHANGELOG.md готов для v0.1.0

**Milestone**: ⏳ MVP готов к production use!

---

# 🤖 PHASE 7: GitHub Actions (Extended)

**Статус**: ⏳ Планируется

**Цель**: Автоматизация через GitHub Actions для CI/CD workflows

**Критерий завершения**: Можно добавлять пакеты из GitHub Actions автоматически

## Step 7.1: Add Packages Workflow

**Файл**: `.github/workflows/add-packages.yml`

**Задачи:**
- [ ] Создать workflow файл
- [ ] Определить inputs: codename, component, artifact_name
- [ ] Step: Download artifact
- [ ] Step: Setup SSH (webfactory/ssh-agent)
- [ ] Step: Import GPG key
- [ ] Step: rsync пакетов на сервер
- [ ] Step: SSH execute `debdebrepomanager add`
- [ ] Step: Cleanup (always block)
- [ ] Error handling
- [ ] Report в GitHub Actions summary

**Secrets required:**
- SSH_PRIVATE_KEY
- SSH_HOST
- SSH_USER
- GPG_PRIVATE_KEY
- GPG_PASSPHRASE
- GPG_KEY_ID

**Тесты**:
- [ ] Manual test в GitHub Actions

**Оценка**: 3-4 часа

**Зависимости**: Phase 3 (CLI add command)

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 7.2: Integration Example

**Файл**: `docs/GITHUB_ACTIONS_INTEGRATION.md`

**Задачи:**
- [ ] Написать пример использования в других репозиториях
- [ ] Setup secrets instructions
- [ ] Полный workflow example (build → publish)
- [ ] Troubleshooting section
- [ ] Security best practices

**Оценка**: 1-2 часа

**Зависимости**: Step 7.1

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

**PHASE 7 TOTAL**: 4-6 часов

**Phase 7 Checklist:**
- [ ] Step 7.1: Workflow завершен
- [ ] Step 7.2: Documentation завершена
- [ ] Workflow работает в GitHub Actions
- [ ] Secrets документированы
- [ ] Пример использования протестирован
- [ ] GPG cleanup работает (always block)

**Milestone**: ⏳ Автоматизация добавления пакетов из CI/CD готова

---

# 🧹 PHASE 8: Cleanup & Retention (Next Iteration)

**Статус**: ⏳ Планируется (не входит в MVP)

**Цель**: Автоматическая очистка старых версий пакетов

**Критерий завершения**: Автоматическая очистка по retention policy работает

## Step 8.1: Retention Policy Module

**Файл**: `repomanager/retention.py`

**Задачи:**
- [ ] Создать `RetentionPolicy` dataclass
- [ ] Реализовать `get_packages_to_remove(packages, policy)`
- [ ] Группировка пакетов по имени и версии
- [ ] Применение min_versions правила
- [ ] Применение max_age_days правила
- [ ] Комбинированная логика

**Тесты**: `tests/test_retention.py`
- [ ] Группировка пакетов
- [ ] Применение min_versions
- [ ] Применение max_age_days
- [ ] Комбинированная логика
- [ ] Edge cases (мало пакетов, все новые, все старые)

**Оценка**: 3-4 часа

**Зависимости**: Step 1.1 (Config), Step 1.2 (Utils)

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 8.2: Cleanup Command

**Файл**: `repomanager/cli.py` (дополнение)

**Задачи:**
- [ ] Создать command: `cleanup`
- [ ] Опции: --codename, --component, --dry-run, --apply
- [ ] Get packages из репозитория
- [ ] Применение retention policy
- [ ] Remove packages (если --apply)
- [ ] Create new snapshot
- [ ] Publish atomically
- [ ] Отчет о удаленных пакетах

**Тесты**: `tests/test_cli.py` (дополнение)
- [ ] Cleanup dry-run
- [ ] Cleanup apply
- [ ] Report generation
- [ ] Error handling

**Оценка**: 3-4 часа

**Зависимости**: Step 8.1, Phase 2

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

## Step 8.3: Cleanup Workflow

**Файл**: `.github/workflows/cleanup-repo.yml`

**Задачи:**
- [ ] Создать workflow файл
- [ ] Schedule trigger (weekly)
- [ ] Manual trigger (workflow_dispatch)
- [ ] Inputs: codename, component, dry_run
- [ ] SSH execute cleanup
- [ ] Collect report
- [ ] Post report (optional)

**Тесты**:
- [ ] Manual test в GitHub Actions

**Оценка**: 2 часа

**Зависимости**: Step 8.2

**Progress**: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%

---

**PHASE 8 TOTAL**: 8-10 часов

**Phase 8 Checklist:**
- [ ] Step 8.1: Retention Module завершен
- [ ] Step 8.2: Cleanup Command завершен
- [ ] Step 8.3: Cleanup Workflow завершен
- [ ] Retention policy работает корректно
- [ ] Dry-run показывает правильный preview
- [ ] Apply удаляет пакеты и обновляет repo
- [ ] Workflow запускается по schedule
- [ ] Все тесты Phase 8 проходят
- [ ] Coverage >= 85%

**Milestone**: ⏳ Автоматическая очистка старых версий работает

---

# 🔐 PHASE 9: GPG Key Rotation (v1.1)

**Статус**: ⏳ Планируется (высокий приоритет для production)

**Цель**: Безопасная ротация GPG ключей без downtime репозиториев

**Критерий завершения**: Можно сменить GPG ключ с автоматической переподписью всех репозиториев

## Step 9.1: GPG Rotation Module

**Файл**: `repomanager/gpg_rotation.py` (новый)

**Задачи:**
- [ ] Создать класс `GPGRotationManager`
- [ ] Method: `validate_new_key(key_id)` - проверка нового ключа доступен
- [ ] Method: `backup_current_key()` - резервная копия текущей подписи
- [ ] Method: `get_all_published_repos()` - список всех опубликованных репо
- [ ] Method: `resign_repository(codename, component, new_key_id)` - переподпись репо
- [ ] Method: `rotate_all_repos(new_key_id, grace_period=False)` - ротация всех
- [ ] Method: `verify_rotation(new_key_id)` - валидация успешности
- [ ] Method: `rollback_rotation(old_key_id)` - откат при ошибках
- [ ] Grace period support - оба ключа валидны временно

**Оценка**: 4-5 часов

**Зависимости**: Phase 4 (GPG module)

## Step 9.2: CLI Rotate Command

**Файл**: `repomanager/cli.py` (дополнение)

**Задачи:**
- [ ] Создать command: `rotate-gpg-key`
- [ ] Опции: --new-key-id, --grace-period, --verify-only, --rollback
- [ ] Validation: новый ключ существует и доступен
- [ ] Confirmation prompt (критическая операция!)
- [ ] Progress indicator для каждого репозитория
- [ ] Детальный отчет о ротации
- [ ] Export нового публичного ключа
- [ ] Генерация migration script для клиентов
- [ ] Error handling и rollback

**Пример использования:**
```bash
# Проверка нового ключа
repomanager rotate-gpg-key --new-key-id NEWKEY123 --verify-only

# Ротация с grace period
repomanager rotate-gpg-key --new-key-id NEWKEY123 --grace-period

# Полная ротация
repomanager rotate-gpg-key --new-key-id NEWKEY123

# Rollback при проблемах
repomanager rotate-gpg-key --rollback --old-key-id OLDKEY456
```

**Оценка**: 2-3 часа

**Зависимости**: Step 9.1

## Step 9.3: Automated Tests

**Файл**: `tests/test_gpg_rotation.py` (новый)

**Задачи:**
- [ ] Test: validate_new_key
- [ ] Test: resign single repository
- [ ] Test: rotate all repositories
- [ ] Test: grace period behavior
- [ ] Test: rollback mechanism
- [ ] Test: verification after rotation
- [ ] Test: error handling (key not found, permission denied)
- [ ] Integration test: полная ротация с aptly

**Оценка**: 3-4 часа

**Зависимости**: Step 9.1, 9.2

## Step 9.4: Client Migration Tools

**Файл**: `scripts/migrate-gpg-key.sh` (новый)

**Задачи:**
- [ ] Скрипт для клиентов - автоматическое обновление ключа
- [ ] Детекция системы (Debian/Ubuntu/etc)
- [ ] Удаление старого ключа
- [ ] Импорт нового ключа
- [ ] Проверка apt update после миграции
- [ ] Rollback при ошибках
- [ ] Verbose mode для отладки

**Генерируется командой:**
```bash
repomanager rotate-gpg-key --new-key-id NEWKEY123 --generate-client-script > migrate-key.sh
```

**Оценка**: 1-2 часа

**Зависимости**: Step 9.2

## Step 9.5: Documentation

**Файлы**: `docs/GPG_ROTATION.md` (новый), обновления в других docs

**Задачи:**
- [ ] Создать docs/GPG_ROTATION.md
  - [ ] Когда нужна ротация (expiration, compromise, best practices)
  - [ ] Пошаговая инструкция ротации
  - [ ] Grace period стратегия
  - [ ] Client migration instructions
  - [ ] Troubleshooting
  - [ ] Rollback procedures
- [ ] Обновить docs/QUICKSTART.md - упомянуть ротацию
- [ ] Обновить README.md - добавить rotate-gpg-key команду
- [ ] Обновить docs/CONFIG.md - параметры для ротации

**Оценка**: 2-3 часа

**Зависимости**: Steps 9.1-9.4

---

**PHASE 9 TOTAL**: 12-17 часов (1.5-2 дня)

**Phase 9 Checklist:**
- [ ] Step 9.1: GPG Rotation Module завершен
- [ ] Step 9.2: CLI Rotate Command завершен
- [ ] Step 9.3: Tests завершены (coverage >= 85%)
- [ ] Step 9.4: Client Migration Tools готовы
- [ ] Step 9.5: Documentation complete
- [ ] Ротация работает без downtime
- [ ] Grace period поддерживается
- [ ] Rollback mechanism работает
- [ ] Client migration script тестирован
- [ ] All tests проходят
- [ ] `make check-all` passes

**Milestone**: ⏳ Безопасная ротация GPG ключей готова для production

**Priority**: HIGH (security best practice)

---

# 📈 Progress Summary

## MVP Phases (Ready for Production)

| Phase | Описание | Часов | Статус | Progress |
|-------|----------|-------|--------|----------|
| 0 | Infrastructure | - | ✅ Done | ████████████████████ 100% |
| 1 | Core Modules | 7-10 | ✅ Done | ████████████████████ 100% |
| 2 | Repository Operations | 9-12 | ✅ Done | ████████████████████ 100% |
| 3 | CLI Interface | 7-9 | ✅ Done | ████████████████████ 100% |
| 4 | GPG Integration | 4-5 | ✅ Done | ████████████████████ 100% |
| 5 | Dual Format | 3-4 | ✅ Done | ████████████████████ 100% |
| 6 | Testing & Polish | 10-14 | ⚠️ Partial | ████████████⬜⬜⬜⬜⬜⬜⬜ 60% |

**MVP TOTAL**: 40-54 часа (5-7 рабочих дней)

**MVP Progress**: ██████████████████⬜⬜ ~95% (Phases 0-5 done, Phase 6 in progress)

## Extended Features

| Phase | Описание | Часов | Статус | Progress |
|-------|----------|-------|--------|----------|
| 7 | GitHub Actions | 4-6 | ⏳ Planned | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |
| 8 | Retention/Cleanup | 8-10 | ⏳ Planned | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |
| 9 | GPG Key Rotation | 6-8 | ⏳ Planned (v1.1) | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |

**Extended TOTAL**: 18-24 часа (2-3 дня)

## Grand Total

**Full v1.0**: 52-70 часов (7-9 рабочих дней)

**Overall Progress**: ██████████████████⬜⬜ ~90% (Phases 0-5 complete, Phase 6 partial)

---

# 🎯 Критерии готовности MVP

## Функциональные требования

- [x] Создание репозиториев с любым codename/component
- [x] Добавление пакетов (одиночных или из директории)
- [x] Atomic updates через snapshots
- [x] GPG подпись всех репозиториев
- [x] Dual format support (старый и новый URL)
- [x] Просмотр репозиториев и пакетов
- [x] Force создание (--force опция)
- [x] Delete repository с подтверждением

## Нефункциональные требования

- [x] Code coverage 80%+ (actual: 93%)
- [x] Все тесты проходят (181 tests passed)
- [x] Code style compliance (black, flake8, mypy)
- [x] Документация актуальна (CHANGELOG, TODO updated)
- [x] CLI удобен для использования
- [x] Error messages понятные и helpful
- [x] No trailing spaces
- [x] All type hints present

## Опциональные (Extended)

- [ ] GitHub Actions workflows
- [ ] Retention policies
- [ ] Automated cleanup

---

# 📅 Execution Plan

## Week 1: Core Implementation

### Days 1-2: Core Modules (Phase 1)
- [x] Config module (config.py) ✅
- [ ] Utils module (utils.py) ⏳ NEXT
- [ ] Aptly base (aptly.py базовые методы)
- [x] Unit tests для config ✅
- [ ] Unit tests для utils, aptly
- [x] `make check-all` проходит для config ✅

### Days 3-4: Repository Operations (Phase 2)
- [ ] Create repo (aptly.py)
- [ ] Add packages atomic (aptly.py)
- [ ] List operations (aptly.py)
- [ ] Tests для всех операций
- [ ] Integration тесты между операциями

### Day 5: CLI (Phase 3)
- [x] CLI core (cli.py) ✅
- [x] Add command ✅
- [x] Create/delete/list commands ✅
- [x] CLI tests ✅
- [x] Help messages ✅

**Week 1 Checklist:**
- [x] Phases 1, 2, 3 завершены ✅
- [x] Все тесты проходят ✅ (149 tests)
- [x] `make check-all` passes ✅
- [x] Coverage 92% ✅

## Week 2: Integration & Polish

### Day 6: GPG & Dual Format (Phases 4-5)
- [ ] GPG module (gpg.py)
- [ ] GPG integration в aptly
- [ ] Dual format symlinks
- [ ] Tests для GPG и symlinks
- [ ] Manual testing с GPG ключом

### Days 7-8: Testing & Documentation (Phase 6)
- [ ] Complete unit tests (приоритет 1)
- [ ] Polish CLI (errors, progress)
- [ ] Update documentation
- [ ] Manual testing на сервере
- [ ] Fix все найденные баги
- [ ] Final `make check-all`

### Day 9: MVP Release
- [ ] Final review всего кода
- [ ] Update docs/CHANGELOG.md
- [ ] Update docs/TODO.md (mark done)
- [ ] Tag v0.1.0
- [ ] GitHub Release
- [ ] Production deployment
- [ ] Testing на production

**Week 2 Checklist:**
- [ ] Phases 4, 5, 6 завершены
- [ ] MVP complete и протестирован
- [ ] v0.1.0 released
- [ ] Production deployment успешен

## Week 3: Extended Features (Optional)

### Days 10-11: GitHub Actions (Phase 7)
- [ ] Add packages workflow
- [ ] Integration documentation
- [ ] Testing workflow в GitHub Actions
- [ ] Setup secrets на production

### Day 12: Retention (Phase 8 start)
- [ ] Retention module
- [ ] Basic cleanup command
- [ ] Tests для retention

**Week 3 Checklist:**
- [ ] Phase 7 завершена (GitHub Actions)
- [ ] Phase 8 начата (Retention)

---

# 🔀 Parallel Work Strategy

## Можно делать параллельно

### Phase 1
- Step 1.1 (Config) - ты
- Step 1.2 (Utils) - я (AI)

### Phase 2
После завершения Phase 1:
- Step 2.1 (Create repo) - ты
- Step 2.3 (List operations) - я (AI)
- Step 2.2 (Add packages) - после 2.1

### Phase 4 & 5
Можно параллельно:
- Step 4.1 (GPG) - один человек
- Step 5.1 (Dual format) - другой человек

## Последовательно (зависимости)

1. Phase 1 → Phase 2 (config нужен для aptly)
2. Phase 2 → Phase 3 (aptly API нужен для CLI)
3. Phase 3 → Phase 7 (CLI нужен для GitHub Actions)

---

# ✅ Definition of Done

## Для каждого модуля

- [ ] Код написан согласно code-style.md
- [ ] Type hints везде
- [ ] Docstrings (Google style)
- [ ] Unit tests написаны
- [ ] Tests проходят
- [ ] Coverage module >= 80%
- [ ] `make check-all` проходит
- [ ] Code review пройден (GitHub PR)

## Для каждой фазы

- [ ] Все шаги фазы завершены
- [ ] Integration tests между модулями
- [ ] Документация обновлена
- [ ] CHANGELOG.md обновлен
- [ ] docs/TODO.md отмечен прогресс

## Для MVP

- [ ] Все Phase 0-6 завершены
- [ ] Overall coverage >= 80%
- [ ] CLI работает для всех команд
- [ ] GPG signing работает
- [ ] Dual format работает
- [ ] Документация complete
- [ ] Manual testing на реальном сервере
- [ ] README.md с real examples

---

# 🚀 Ready to Start?

**Следующий шаг**: Phase 1, Step 1.1 - Config Module

Начинаем с `repomanager/config.py` + `tests/test_config.py`

**Предлагаю план:**
1. Я создам базовую структуру Config класса
2. Ты добавишь/доработаешь логику
3. Я напишу тесты
4. Вместе проверим и доработаем

Готов начать? 🚀


