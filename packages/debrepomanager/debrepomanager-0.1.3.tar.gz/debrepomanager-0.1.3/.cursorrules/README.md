# Cursor Rules for Debian Repository Manager

Правила и guidelines для работы с проектом через Cursor AI.

## 📁 Структура правил

Правила разбиты по категориям для удобства навигации и обновления:

| Файл | Описание |
|------|----------|
| [git-workflow.md](git-workflow.md) | 🔒 GIT WORKFLOW - НИКОГДА НЕ ПУШИТЬ В MAIN! (КРИТИЧНО!) |
| [mvp-requirements.md](mvp-requirements.md) | 🎯 MVP requirements и scope (важно!) |
| [docker-python-versions.md](docker-python-versions.md) | Docker Compose v2 и Python versions requirements |
| [code-style.md](code-style.md) | Code style guidelines (Python, formatting, type hints) |
| [testing.md](testing.md) | Testing requirements и best practices |
| [development.md](development.md) | Development workflow (git, commits, pre-commit) |
| [architecture.md](architecture.md) | Architecture guidelines и design patterns |
| [aptly-integration.md](aptly-integration.md) | Aptly integration patterns |
| [documentation.md](documentation.md) | Documentation guidelines |
| [error-handling.md](error-handling.md) | Error handling patterns |
| [security.md](security.md) | Security considerations |
| [pitfalls.md](pitfalls.md) | Common pitfalls и anti-patterns |
| [quick-reference.md](quick-reference.md) | Quick reference и file paths |

## 🎯 Project Overview

**Debian Repository Manager** - система управления набором Debian-like репозиториев на базе aptly с поддержкой множественных дистрибутивов, архитектур и коллекций.

### Key Technologies
- **Backend**: aptly (Debian repository management)
- **Language**: Python 3.11+ (tested on 3.11, 3.12, 3.13)
- **CLI**: click
- **Testing**: pytest (194 tests, 93% coverage)
- **Code Quality**: black, flake8, mypy, isort

### Project Structure
```
repomanager/
├── docs/               # Документация
├── repomanager/        # Основной Python пакет
├── tests/              # Тесты
├── .github/workflows/  # GitHub Actions
└── config.yaml.example # Конфигурация
```

## 🚀 Quick Start для AI

### При начале разработки
1. **ПЕРВЫМ ДЕЛОМ**: Читай [mvp-requirements.md](mvp-requirements.md) для понимания scope
2. Открой docs/IMPLEMENTATION_PLAN.md - смотри текущую фазу
3. Следуй чекбоксам в плане

### При написании кода
1. Читай [code-style.md](code-style.md) для форматирования
2. Следуй [testing.md](testing.md) - **ВСЕГДА** добавляй тесты (TDD!)
3. Используй [architecture.md](architecture.md) для дизайна
4. Проверяй [pitfalls.md](pitfalls.md) - что НЕ делать
5. См. [aptly-integration.md](aptly-integration.md) для aptly patterns

### При работе с документацией
1. Читай [documentation.md](documentation.md) для guidelines
2. Используй [quick-reference.md](quick-reference.md) для навигации
3. Следуй File Paths Convention (всегда `docs/FILE.md`)

### Перед commit (обязательно!)
Проверь [development.md](development.md) для pre-commit checklist:
```bash
make format      # Black formatting
make lint        # flake8
make type-check  # mypy
make test        # pytest (coverage 80%+!)
make check-all   # Все проверки
```

**НЕ коммить** если `make check-all` не проходит!

## 📚 Документация

Вся документация в папке `docs/`:
- **docs/README.md** - навигация по всей документации
- **docs/IMPLEMENTATION_PLAN.md** - финальный план реализации (START HERE!)
- **docs/PHASES_OVERVIEW.md** - визуальный обзор фаз
- **docs/QUICKSTART.md** - быстрый старт за 5 минут
- **docs/ARCHITECTURE.md** - архитектурные решения
- **docs/IMPLEMENTATION_STEPS.md** - примеры кода для каждого модуля
- **docs/DEVELOPMENT.md** - руководство для разработчиков
- **docs/CONFIG.md** - детальное описание конфигурации
- **docs/APT_CONFIGURATION.md** - настройка APT для клиентов
- **docs/DUAL_FORMAT.md** - поддержка двух форматов URL
- **docs/WORKFLOWS.md** - GitHub Actions workflows
- **docs/TODO.md** - checklist задач

## 🔍 Навигация по правилам

### Для нового разработчика
1. [README.md](README.md) (этот файл) - начало
2. [code-style.md](code-style.md) - style guide
3. [testing.md](testing.md) - как писать тесты
4. [development.md](development.md) - workflow

### Для опытного разработчика
1. [quick-reference.md](quick-reference.md) - быстрая навигация
2. [architecture.md](architecture.md) - design patterns
3. [pitfalls.md](pitfalls.md) - что НЕ делать

### Для AI ассистента
Все файлы актуальны и должны соблюдаться при генерации кода.

## 🎓 Принципы проекта

1. **Code Quality First**: Black, flake8, mypy - обязательны перед каждым commit
2. **Test Everything**: минимум 80% coverage для MVP, критичные модули 85%+
3. **Document Everything**: docstrings (Google style), type hints везде, обновление docs/
4. **Security Matters**: GPG ключи (passphrase через getpass), SSH, paths validation
5. **Aptly Multi-Root**: изоляция через отдельные roots для каждого codename
6. **Dual Format Support**: старый и новый URL форматы работают одновременно через symlinks
7. **Atomic Updates**: все изменения через snapshots (мгновенное переключение)

## 🏁 Current Status

**Версия**: v0.1.0 ✅ (Released 2025-11-03)

**MVP Progress**: 95% (Phases 0-5 complete)

**Следующая итерация**: Phase 7-8 (GitHub Actions, Retention policies)

**См.**: docs/reports/PROJECT_STATUS.md для деталей

## 📞 Контакты

- **Issues**: https://github.com/jethome/repomanager/issues
- **Docs**: docs/README.md
- **Help**: `make help`

