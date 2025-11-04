# Implementation Phases - Visual Overview

Визуальный обзор всех фаз разработки Debian Repository Manager.

## 📊 Общая картина

```
Phase 0 ✅ DONE
    ↓
Phase 1: Core Modules (7-10h)
    ↓
Phase 2: Repository Operations (9-12h)
    ↓
Phase 3: CLI Interface (7-9h)
    ↓
┌───────┴────────┐
│                │
Phase 4:         Phase 5:
GPG (4-5h)       Dual Format (3-4h)
│                │
└───────┬────────┘
        ↓
Phase 6: Testing & Polish (10-14h)
        ↓
    🎉 MVP READY (40-54h)
        ↓
Phase 7: GitHub Actions (4-6h)
        ↓
Phase 8: Retention/Cleanup (8-10h)
        ↓
    🚀 v1.0 COMPLETE (52-70h)
```

## ✅ Phase 0: Infrastructure (DONE)

**Время**: ✅ Завершено

**Deliverables:**
- ✅ Project structure
- ✅ Documentation (14 docs)
- ✅ Cursor rules (11 files)
- ✅ CI workflows (4 workflows)
- ✅ Python setup (requirements, setup.py, pyproject.toml)
- ✅ Testing setup (pytest, coverage)

---

## 🔧 Phase 1: Core Modules

**Время**: 7-10 часов

**Цель**: Базовые модули для работы системы

### Deliverables:

| Модуль | Файл | Функции | Тесты | Часы |
|--------|------|---------|-------|------|
| Config | config.py | Load, merge, validate, accessors | test_config.py | 3-4 |
| Utils | utils.py | Logging, .deb parsing, version compare | test_utils.py | 2-3 |
| Aptly Base | aptly.py | _run_aptly(), naming, config path | test_aptly.py | 2-3 |

### Success Criteria:
- [ ] Config loads from YAML
- [ ] Config merges repo + /etc config
- [ ] Utils parse .deb correctly
- [ ] Utils compare versions correctly
- [ ] Aptly _run_aptly() calls aptly with -config
- [ ] All tests pass
- [ ] Coverage >= 85%

---

## 📦 Phase 2: Repository Operations

**Время**: 9-12 часов

**Цель**: CRUD операции с репозиториями

### Deliverables:

| Операция | Метод | Описание | Часы |
|----------|-------|----------|------|
| Create | create_repo() | Create aptly repo + initial publish | 3-4 |
| Add | add_packages() | Add packages atomically via snapshot | 4-5 |
| List | list_repos(), list_packages() | Query repositories and packages | 2-3 |

### Success Criteria:
- [ ] Создает aptly.conf для нового codename
- [ ] Создает local repo в aptly
- [ ] Initial publish с пустым snapshot
- [ ] Добавляет пакеты и создает snapshot
- [ ] Atomic switch на новый snapshot
- [ ] Cleanup старых snapshots
- [ ] Список репо и пакетов работает
- [ ] All tests pass with mocks
- [ ] Coverage >= 85%

---

## 🖥️ Phase 3: CLI Interface

**Время**: 7-9 часов

**Цель**: Удобный CLI для всех операций

### Deliverables:

| Команда | Описание | Часы |
|---------|----------|------|
| CLI core | click setup, global options | 1-2 |
| add | Add packages to repo | 2-3 |
| create-repo | Create new repository | 1-2 |
| delete-repo | Delete repository | 1 |
| list | List repos/packages | 1-2 |

### Success Criteria:
- [ ] `debrepomanager --help` работает
- [ ] `debdebrepomanager add --package-dir /path` работает
- [ ] `debdebrepomanager create-repo --force` работает
- [ ] `debdebrepomanager list` показывает репо
- [ ] `debdebrepomanager delete-repo --confirm` работает
- [ ] Error messages понятные
- [ ] Progress output для долгих операций
- [ ] All CLI tests pass
- [ ] Coverage >= 75%

---

## 🔐 Phase 4: GPG Integration

**Время**: 4-5 часов

**Цель**: Обязательная GPG подпись всех репозиториев

### Deliverables:

| Компонент | Файл | Функции | Часы |
|-----------|------|---------|------|
| GPG Manager | gpg.py | check_key, get_passphrase, test_signing | 2-3 |
| Aptly Integration | aptly.py | Add -gpg-key to publish commands | 2 |

### Assumptions:
- GPG ключ уже импортирован в user's keyring
- Если ключ с паролем - запрашиваем через getpass
- gpg-agent может кешировать (опционально)

### Success Criteria:
- [ ] Проверяет наличие GPG ключа перед операциями
- [ ] Запрашивает passphrase если нужно
- [ ] Все publish операции с -gpg-key
- [ ] aptly verify проходит для published репо
- [ ] Tests с mock gpg
- [ ] Coverage >= 80%

---

## 🔄 Phase 5: Dual Format Support

**Время**: 3-4 часа

**Цель**: Поддержка старого и нового форматов URL одновременно

### Deliverables:

| Компонент | Файл | Функции | Часы |
|-----------|------|---------|------|
| Symlink creation | aptly.py | _create_dual_format_symlinks() | 2-3 |
| Setup script | scripts/setup-dual-format.sh | Initial symlinks setup | 1 |

### Success Criteria:
- [ ] Symlinks создаются при publish
- [ ] Старый формат: `deb http://repo.jethome.ru bookworm component` работает
- [ ] Новый формат: `deb http://repo.jethome.ru/bookworm component main` работает
- [ ] Скрипт setup-dual-format.sh создает symlinks для всех codenames
- [ ] Tests проверяют создание symlinks
- [ ] curl тесты обоих форматов работают

---

## ✅ Phase 6: Testing & Polish

**Время**: 10-14 часов

**Цель**: Полное покрытие тестами, готовность к production

### Deliverables:

| Задача | Описание | Часы |
|--------|----------|------|
| Unit Tests | Complete coverage для всех модулей | 6-8 |
| CLI Polish | Error messages, progress, help | 2-3 |
| Documentation | Update с real examples | 2-3 |

### Testing Breakdown:

**Обязательно для MVP:**
- ✅ test_config.py - полное покрытие (90%+)
- ✅ test_aptly.py - все операции (85%+)
- ✅ test_utils.py - все функции (80%+)
- ✅ test_gpg.py - GPG операции (80%+)
- ✅ test_cli.py - все команды (75%+)

**Можно отложить:**
- ⏳ Integration tests с реальным aptly
- ⏳ Performance tests
- ⏳ Stress tests (большое количество пакетов)

### Success Criteria:
- [ ] Overall coverage >= 80%
- [ ] Critical modules (config, aptly) >= 85%
- [ ] All tests pass
- [ ] `make check-all` проходит
- [ ] CLI tested manually на реальном сервере
- [ ] Documentation актуальна
- [ ] README examples работают

---

## 🎉 MVP MILESTONE

**После Phase 6 - Ready for Production!**

**Что можно делать:**
- ✅ Создавать репозитории
- ✅ Добавлять пакеты (атомарно)
- ✅ Просматривать репо и пакеты
- ✅ Удалять репозитории
- ✅ Все с GPG подписью
- ✅ Оба формата URL работают
- ✅ Ручное управление через CLI

**Что НЕ входит в MVP:**
- ⏳ GitHub Actions автоматизация
- ⏳ Автоматический cleanup старых версий
- ⏳ Retention policies

**Оценка MVP**: 40-54 часа = **5-7 рабочих дней**

---

## 🤖 Phase 7: GitHub Actions

**Время**: 4-6 часов

**Цель**: Автоматизация добавления пакетов из CI/CD

### Deliverables:

| Workflow | Файл | Функции | Часы |
|----------|------|---------|------|
| Add Packages | add-packages.yml | rsync + SSH add | 3-4 |
| Documentation | GITHUB_ACTIONS_INTEGRATION.md | Guide + examples | 1-2 |

### Workflow Steps:
1. Download artifact
2. Setup SSH
3. Setup GPG (import key)
4. rsync packages
5. SSH execute `debdebrepomanager add`
6. Cleanup (always)

### Success Criteria:
- [ ] Workflow работает в GitHub Actions
- [ ] Secrets документированы
- [ ] Пример использования в docs
- [ ] Tested в реальном repo
- [ ] Cleanup GPG ключа работает (always block)

---

## 🧹 Phase 8: Retention & Cleanup

**Время**: 8-10 часов

**Цель**: Автоматическая очистка старых версий

### Deliverables:

| Компонент | Файл | Функции | Часы |
|-----------|------|---------|------|
| Retention Logic | retention.py | RetentionPolicy, get_packages_to_remove | 3-4 |
| Cleanup Command | cli.py | cleanup --dry-run, --apply | 3-4 |
| Cleanup Workflow | cleanup-repo.yml | Schedule weekly cleanup | 2 |

### Success Criteria:
- [ ] Retention policy применяется корректно
- [ ] Dry-run показывает что будет удалено
- [ ] Apply удаляет пакеты и создает новый snapshot
- [ ] Workflow запускается по schedule
- [ ] Tests для retention logic
- [ ] Coverage >= 85%

---

## 📈 Timeline Summary

### Sprint 1 (Week 1): Core & CLI
- **Days 1-2**: Phase 1 (Core modules)
- **Days 3-4**: Phase 2 (Repository ops)
- **Day 5**: Phase 3 (CLI)

### Sprint 2 (Week 2): Integration & MVP
- **Day 6**: Phase 4 (GPG) + Phase 5 (Dual format)
- **Days 7-8**: Phase 6 (Testing & Polish)
- **Day 9**: MVP Release v0.1.0

### Sprint 3 (Week 3): Extended Features
- **Days 10-11**: Phase 7 (GitHub Actions)
- **Day 12**: Phase 8 start (Retention)

**MVP**: End of Week 2
**v1.0**: End of Week 3

---

## 🎯 MVP Features Checklist

### Repository Management
- [ ] Create repository (`create-repo`)
- [ ] Delete repository (`delete-repo --confirm`)
- [ ] List repositories (`list`)
- [ ] Force creation (`--force`)
- [ ] Auto-create при add (если включено в config)

### Package Management
- [ ] Add single package (`add --packages file.deb`)
- [ ] Add multiple packages (`add --packages *.deb`)
- [ ] Add from directory (`add --package-dir /path/`)
- [ ] Recursive search в directory
- [ ] Atomic updates (snapshot switch)

### GPG Integration
- [ ] GPG signing всех публикаций
- [ ] Check key availability
- [ ] Passphrase prompt (если нужно)
- [ ] Verify signatures работает

### Dual Format Support
- [ ] Старый формат работает: `deb http://repo.jethome.ru codename component`
- [ ] Новый формат работает: `deb http://repo.jethome.ru/codename component main`
- [ ] Symlinks создаются автоматически
- [ ] Script для initial setup

### Code Quality
- [ ] Coverage >= 80%
- [ ] All tests pass
- [ ] Black formatting
- [ ] flake8 clean
- [ ] mypy clean
- [ ] No trailing spaces

### Documentation
- [ ] README актуален
- [ ] QUICKSTART работает
- [ ] CONFIG.md complete
- [ ] APT_CONFIGURATION.md с примерами
- [ ] DUAL_FORMAT.md техническая документация

---

## 🚀 Execution Strategy

### Parallel Work (где возможно)

**Week 1, Days 1-2:**
- Ты: Config module (3-4h)
- AI: Utils module (2-3h)
- Together: Review и интеграция

**Week 1, Days 3-4:**
- Ты: Create repo (3-4h)
- AI: List operations (2-3h)
- Together: Add packages (4-5h)

**Week 1, Day 5:**
- Together: CLI implementation

**Week 2, Day 6:**
- Parallel: GPG (один) + Dual format (другой)

### Sequential Work (зависимости)

**Must be sequential:**
- Phase 1 → Phase 2 (aptly нужен config)
- Phase 2 → Phase 3 (CLI нужен aptly API)
- Phases 1-5 → Phase 6 (тесты нужны все модули)

---

## 📋 Daily Goals

### Day 1: Config & Utils
- [ ] Implement config.py
- [ ] Write test_config.py
- [ ] Implement utils.py
- [ ] Write test_utils.py
- [ ] `make check-all` passes

### Day 2: Aptly Base
- [ ] Implement aptly.py base
- [ ] Write test_aptly.py base
- [ ] Integration test config + aptly
- [ ] `make check-all` passes

### Day 3: Create Repository
- [ ] Implement create_repo()
- [ ] Create aptly.conf generation
- [ ] Tests for create
- [ ] `make check-all` passes

### Day 4: Add Packages
- [ ] Implement add_packages() with snapshots
- [ ] Implement list operations
- [ ] Tests for add and list
- [ ] `make check-all` passes

### Day 5: CLI
- [ ] Implement CLI core (click)
- [ ] Implement all commands
- [ ] CLI integration tests
- [ ] Manual testing
- [ ] `make check-all` passes

### Day 6: GPG & Dual Format
- [ ] Implement gpg.py
- [ ] Integrate в aptly.py
- [ ] Implement dual format symlinks
- [ ] Tests
- [ ] `make check-all` passes

### Day 7-8: Testing & Polish
- [ ] Complete unit tests
- [ ] Polish CLI (errors, progress)
- [ ] Update documentation
- [ ] Manual testing на сервере
- [ ] Fix все найденные баги
- [ ] `make check-all` passes

### Day 9: MVP Release
- [ ] Final review
- [ ] Update CHANGELOG
- [ ] Tag v0.1.0
- [ ] GitHub Release
- [ ] Deploy на production сервер

---

## 🎯 Definition of Done

### For Each Module
- [ ] Code написан согласно .cursorrules/code-style.md
- [ ] Type hints везде
- [ ] Docstrings (Google style) везде
- [ ] Unit tests >= 80% coverage
- [ ] Tests проходят
- [ ] `make check-all` passes
- [ ] PR создан и review пройден

### For Each Phase
- [ ] Все steps завершены
- [ ] Integration между модулями работает
- [ ] Documentation обновлена
- [ ] CHANGELOG.md обновлен
- [ ] docs/TODO.md прогресс отмечен
- [ ] Manual testing пройдено

### For MVP (Phase 6 complete)
- [ ] Все Phases 0-6 завершены
- [ ] Overall coverage >= 80%
- [ ] CLI работает для всех команд
- [ ] GPG signing работает
- [ ] Dual format работает
- [ ] Документация complete и актуальна
- [ ] Manual testing на реальном сервере пройдено
- [ ] README.md с working examples
- [ ] Ready для production deployment

---

## 🔧 Quick Reference

### Команды для разработки
```bash
make install-dev    # Setup окружения
make test           # Run tests
make check-all      # All checks
```

### Документация
- **Этот файл** - обзор фаз
- **IMPLEMENTATION_PLAN.md** - детальный план каждой фазы
- **IMPLEMENTATION_STEPS.md** - примеры кода
- **TODO.md** - checklist задач

### Начать разработку
```bash
# Start Phase 1
cd repomanager
vim repomanager/config.py
# См. docs/IMPLEMENTATION_STEPS.md для примеров
```

---

## 🏁 Next Action

**Начинаем Phase 1, Step 1.1: Config Module**

Файлы:
- `repomanager/config.py`
- `tests/test_config.py`

См. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) для детального описания.

**Готов начать? 🚀**


