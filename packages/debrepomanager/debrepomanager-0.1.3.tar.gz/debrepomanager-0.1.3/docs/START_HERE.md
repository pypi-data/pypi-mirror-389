# 🚀 START HERE - Debian Repository Manager v0.1.0

## Что это?

**Debian Repository Manager** - система управления Debian репозиториями для множественных дистрибутивов.

**Статус**: ✅ MVP v0.1.0 готов и выпущен! (95% complete)

---

## 🎯 Для новых пользователей

### Хочу использовать репоманager?

1. **[QUICKSTART.md](QUICKSTART.md)** - Установка и первый репозиторий за 5 минут
2. **[../README.md](../README.md)** - Все CLI команды с примерами
3. **[CONFIG.md](CONFIG.md)** - Настройка конфигурации
4. **[APT_CONFIGURATION.md](APT_CONFIGURATION.md)** - Настройка клиентов

### Хочу развернуть на сервере?

1. **[QUICKSTART.md](QUICKSTART.md#установка-на-сервере)** - Установка
2. **[CONFIG.md](CONFIG.md)** - Создание config.yaml
3. **[DUAL_FORMAT.md](DUAL_FORMAT.md)** - Настройка dual format
4. **[../README.md](../README.md#troubleshooting)** - Решение проблем

---

## 🔧 Для разработчиков

### Хочу внести вклад?

1. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Setup окружения
2. **[TODO.md](TODO.md)** - Актуальные задачи
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Как устроен проект
4. **[IMPLEMENTATION_STEPS.md](IMPLEMENTATION_STEPS.md)** - Примеры кода

### Хочу понять архитектуру?

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Ключевые решения
2. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Структура модулей
3. **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - План реализации
4. **[DUAL_FORMAT.md](DUAL_FORMAT.md)** - Dual format tech details

---

## 📊 Текущее состояние проекта

### ✅ Что готово (Phases 0-5):

- ✅ **Core Modules**: config, utils, aptly, gpg, cli (100%)
- ✅ **CLI Commands**: add, create-repo, delete-repo, list (100%)
- ✅ **GPG Integration**: Автоматическая подпись (100%)
- ✅ **Dual Format**: Поддержка старого и нового URL (100%)
- ✅ **Tests**: 183 unit + 11 integration (93% coverage)
- ✅ **CI/CD**: Все checks проходят (100%)

### ⏳ В разработке (Phases 7-8):

- Phase 7: GitHub Actions для production
- Phase 8: Retention policies с cleanup

### 📈 MVP Progress: 95%

---

## 🚀 Quick Start

### Для пользователей:

```bash
# Установка
pip install git+https://github.com/jethome-iot/repomanager.git@v0.1.0

# Создание репозитория
debrepomanager create-repo --codename bookworm --component jethome-tools

# Добавление пакетов
debrepomanager add --codename bookworm --component jethome-tools --package-dir /path/to/packages/
```

### Для разработчиков:

```bash
# Клонирование
git clone https://github.com/jethome-iot/repomanager.git
cd repomanager

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Тесты
pytest tests/ -k "not integration"  # Unit tests (локально)
# Integration tests прогоняются в CI через Docker
```

---

## 📚 Полная документация

См. **[docs/README.md](README.md)** для полной навигации по всем документам.

### Ключевые документы:

| Документ | Описание |
|----------|----------|
| [README.md](README.md) | Навигация по документации |
| [QUICKSTART.md](QUICKSTART.md) | Быстрый старт |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура |
| [TODO.md](TODO.md) | Текущие задачи |
| [CHANGELOG.md](CHANGELOG.md) | История изменений |

### Отчеты о состоянии:

| Отчет | Описание |
|-------|----------|
| [reports/ИТОГОВЫЙ_АНАЛИЗ.md](reports/ИТОГОВЫЙ_АНАЛИЗ.md) | Анализ проекта |
| [reports/PROJECT_STATUS.md](reports/PROJECT_STATUS.md) | Статус проекта |
| [reports/CI_SUCCESS_REPORT.md](reports/CI_SUCCESS_REPORT.md) | CI результаты |

---

## 🔗 Ссылки

- **Repository**: https://github.com/jethome-iot/repomanager
- **Release v0.1.0**: https://github.com/jethome-iot/repomanager/releases/tag/v0.1.0
- **Issues**: https://github.com/jethome-iot/repomanager/issues
- **Discussions**: https://github.com/jethome-iot/repomanager/discussions

---

## 💡 Получить помощь

- **Bug reports**: [GitHub Issues](https://github.com/jethome-iot/repomanager/issues)
- **Feature requests**: [GitHub Discussions](https://github.com/jethome-iot/repomanager/discussions)
- **Email**: support@jethome.ru

---

**Готовы начать? См. [QUICKSTART.md](QUICKSTART.md)! 🚀**

