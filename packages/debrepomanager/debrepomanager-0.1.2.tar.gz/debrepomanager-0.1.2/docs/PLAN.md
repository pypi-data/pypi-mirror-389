# Debian Repository Manager - План реализации (Original)

> ⚠️ **Актуальный план**: См. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) для финального детального плана с учетом всех уточнений.
>
> Этот документ сохранен как reference оригинального планирования.

## Обзор

Система управления Debian репозиториями на базе aptly с поддержкой:
- Множественных дистрибутивов (bookworm, noble, trixie, jammy и т.д.)
- Множественных архитектур (amd64, arm64, riscv64)
- Множественных компонентов/коллекций (jethome-tools, jethome-armbian и т.д.)
- Атомарных обновлений через snapshots
- GPG подписи
- GitHub Actions интеграции

## Фазы реализации

### Фаза 1: Базовая инфраструктура (независимые шаги)

#### Шаг 1.1: Структура проекта
**Статус**: Pending
**Зависимости**: Нет
**Можно выполнять параллельно**: со всеми шагами Фазы 1

Создать:
```
repomanager/
├── README.md
├── ARCHITECTURE.md
├── requirements.txt
├── setup.py
├── config.yaml.example
├── repomanager/
│   ├── __init__.py
│   ├── cli.py
│   ├── aptly.py
│   ├── config.py
│   ├── retention.py
│   ├── gpg.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_retention.py
│   ├── test_config.py
│   └── test_aptly.py
└── .github/
    └── workflows/
        ├── add-packages.yml
        ├── cleanup-repo.yml
        └── create-repo.yml
```

#### Шаг 1.2: Конфигурация (config.yaml.example)
**Статус**: Pending
**Зависимости**: Нет
**Можно выполнять параллельно**: с любыми шагами Фазы 1

Создать пример конфигурации с описанием всех параметров:
- GPG настройки
- Пути aptly
- Retention policies (default + overrides)
- Список codenames/components/architectures
- Auto-create опция

#### Шаг 1.3: Dependencies (requirements.txt, setup.py)
**Статус**: Pending
**Зависимости**: Нет
**Можно выполнять параллельно**: с любыми шагами Фазы 1

Определить зависимости:
- PyYAML (конфигурация)
- click или argparse (CLI)
- python-debian (парсинг .deb метаданных)
- subprocess/sh (вызов aptly)

---

### Фаза 2: Core модули (частично параллельные)

#### Шаг 2.1: Config module (config.py)
**Статус**: Pending
**Зависимости**: Шаг 1.3 (requirements.txt)
**Можно выполнять параллельно**: с Шагом 2.2, 2.3

Реализовать:
- Загрузка YAML конфигурации
- Мержинг конфигов (репозиторий + сервер)
- Валидация параметров
- Получение retention policy для компонента
- Получение списка архитектур/codenames/components

```python
class Config:
    def load(self, config_paths: List[str])
    def get_retention_policy(self, component: str) -> RetentionPolicy
    def get_aptly_root(self, codename: str) -> str
    def get_publish_path(self, codename: str, component: str) -> str
```

#### Шаг 2.2: Utils module (utils.py)
**Статус**: Pending
**Зависимости**: Нет
**Можно выполнять параллельно**: с любыми шагами Фазы 2

Реализовать:
- Логирование (настраиваемый logger)
- Парсинг версий пакетов (debian version comparison)
- Получение метаданных из .deb файлов
- Timestamp helpers

#### Шаг 2.3: Aptly wrapper (aptly.py)
**Статус**: Pending
**Зависимости**: Шаг 2.1 (config.py)
**Можно выполнять параллельно**: с Шагом 2.2

Реализовать класс AptlyManager:
- Работа с multi-root (разные директории для разных codenames)
- Создание/удаление локальных репозиториев
- Добавление пакетов в репозиторий
- Создание snapshots
- Публикация snapshots
- Переключение published snapshots (атомарность)
- Список репозиториев/snapshots/published
- Удаление старых snapshots

```python
class AptlyManager:
    def __init__(self, config: Config)
    def create_repo(self, codename: str, component: str, architectures: List[str])
    def add_packages(self, codename: str, component: str, packages: List[str])
    def create_snapshot(self, codename: str, component: str, name: str)
    def publish_snapshot(self, codename: str, component: str, snapshot: str)
    def switch_published(self, codename: str, component: str, snapshot: str)
    def list_packages(self, codename: str, component: str) -> List[PackageInfo]
    def cleanup_snapshots(self, codename: str, component: str, keep: int)
```

---

### Фаза 3: Retention и GPG (независимые)

#### Шаг 3.1: Retention logic (retention.py)
**Статус**: Pending
**Зависимости**: Шаг 2.1 (config.py), Шаг 2.2 (utils.py)
**Можно выполнять параллельно**: с Шагом 3.2

Реализовать:
- Класс RetentionPolicy (min_versions, max_age_days)
- Анализ списка пакетов по версиям
- Определение пакетов для удаления на основе политики
- Учет зависимостей между версиями

```python
class RetentionPolicy:
    min_versions: int
    max_age_days: int

    def get_packages_to_remove(self, packages: List[PackageInfo]) -> List[PackageInfo]
```

#### Шаг 3.2: GPG integration (gpg.py)
**Статус**: Pending
**Зависимости**: Шаг 2.1 (config.py)
**Можно выполнять параллельно**: с Шагом 3.1

Реализовать:
- Проверка наличия GPG ключа
- Проверка gpg-agent
- Импорт ключа (для GitHub Actions)
- Подпись репозиториев через aptly
- Cleanup импортированных ключей

```python
class GPGManager:
    def __init__(self, config: Config)
    def check_key_available(self, key_id: str) -> bool
    def import_key(self, key_data: str, passphrase: str)
    def cleanup_key(self, key_id: str)
    def configure_aptly_signing(self) -> Dict[str, str]
```

---

### Фаза 4: CLI команды (частично параллельные)

#### Шаг 4.1: CLI core (cli.py)
**Статус**: Pending
**Зависимости**: Шаг 2.1 (config.py)
**Блокирует**: все остальные шаги Фазы 4

Реализовать:
- Entry point
- Парсинг аргументов (argparse/click)
- Routing команд
- Общие опции (--config, --verbose, --dry-run)
- Error handling и exit codes

```python
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # add, create-repo, delete-repo, list, verify, cleanup
```

#### Шаг 4.2: Add command
**Статус**: Pending
**Зависимости**: Шаг 4.1 (cli.py), Шаг 2.3 (aptly.py), Шаг 3.2 (gpg.py)
**Можно выполнять параллельно**: с Шагом 4.3, 4.4

Реализовать команду add:
- Принимает --codename, --component
- Принимает --packages (список файлов) или --package-dir (директория)
- Сканирование директории (рекурсивно для *.deb)
- Проверка существования репозитория (auto-create если включено)
- Добавление пакетов через aptly
- Создание snapshot с timestamp
- Атомарная публикация через switch
- Cleanup старых snapshots

```bash
debrepomanager add --codename bookworm --component jethome-tools --packages pkg1.deb pkg2.deb
debrepomanager add --codename bookworm --component jethome-tools --package-dir /path/to/packages/
```

#### Шаг 4.3: Repository management commands
**Статус**: Pending
**Зависимости**: Шаг 4.1 (cli.py), Шаг 2.3 (aptly.py), Шаг 3.2 (gpg.py)
**Можно выполнять параллельно**: с Шагом 4.2, 4.4

Реализовать команды:
- `create-repo`: создание нового репозитория
- `delete-repo`: удаление репозитория (с подтверждением)
- `list`: список репозиториев/пакетов
- `verify`: проверка консистентности

```bash
debrepomanager create-repo --codename noble --component jethome-armbian
debrepomanager delete-repo --codename noble --component jethome-armbian --confirm
debrepomanager list --codename bookworm
repomanager verify --codename bookworm --component jethome-tools
```

#### Шаг 4.4: Cleanup command
**Статус**: Pending
**Зависимости**: Шаг 4.1 (cli.py), Шаг 2.3 (aptly.py), Шаг 3.1 (retention.py)
**Можно выполнять параллельно**: с Шагом 4.2, 4.3

Реализовать команду cleanup:
- Принимает --codename, --component (опционально для всех)
- Применяет retention policy
- Dry-run режим по умолчанию
- Удаление устаревших пакетов
- Создание нового snapshot
- Атомарная публикация
- Отчет о удаленных пакетах

```bash
repomanager cleanup --codename bookworm --component jethome-tools --dry-run
repomanager cleanup --codename bookworm --component jethome-tools --apply
repomanager cleanup --apply  # для всех репозиториев
```

---

### Фаза 5: GitHub Actions (независимые workflow)

#### Шаг 5.1: Add packages workflow
**Статус**: Pending
**Зависимости**: Шаг 4.2 (add command)
**Можно выполнять параллельно**: с Шагом 5.2, 5.3

Создать `.github/workflows/add-packages.yml`:
- Trigger: workflow_dispatch (manual) + workflow_call (reusable)
- Inputs: codename, component, artifact_name или packages_path
- Steps:
  1. Checkout репозитория (для скриптов)
  2. Download artifact (если указан)
  3. Setup SSH ключей из secrets
  4. Setup GPG ключей из secrets (import)
  5. rsync пакетов на сервер во временную директорию
  6. SSH: выполнение `debdebrepomanager add`
  7. Cleanup: удаление временных файлов, GPG keys
  8. Report: summary в GitHub Actions

```yaml
name: Add Packages to Repository
on:
  workflow_dispatch:
    inputs:
      codename: ...
      component: ...
      artifact_name: ...
```

#### Шаг 5.2: Cleanup workflow
**Статус**: Pending
**Зависимости**: Шаг 4.4 (cleanup command)
**Можно выполнять параллельно**: с Шагом 5.1, 5.3

Создать `.github/workflows/cleanup-repo.yml`:
- Trigger: schedule (weekly), workflow_dispatch
- Inputs: codename (optional), component (optional), dry_run (default: false)
- Steps:
  1. Setup SSH
  2. SSH: выполнение `debrepomanager cleanup`
  3. Collect report
  4. Post report as comment/issue (optional)

```yaml
name: Cleanup Old Packages
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM
  workflow_dispatch:
    inputs:
      codename: ...
      dry_run: ...
```

#### Шаг 5.3: Create repository workflow
**Статус**: Pending
**Зависимости**: Шаг 4.3 (repository management)
**Можно выполнять параллельно**: с Шагом 5.1, 5.2

Создать `.github/workflows/create-repo.yml`:
- Trigger: workflow_dispatch
- Inputs: codename, component
- Steps:
  1. Setup SSH, GPG
  2. SSH: выполнение `debdebrepomanager create-repo`
  3. Verify creation

```yaml
name: Create Repository
on:
  workflow_dispatch:
    inputs:
      codename: ...
      component: ...
```

---

### Фаза 6: Тестирование и документация (независимые)

#### Шаг 6.1: Unit tests
**Статус**: Pending
**Зависимости**: Шаг 3.1 (retention.py), Шаг 2.1 (config.py), Шаг 2.3 (aptly.py)
**Можно выполнять параллельно**: с Шагом 6.2

Написать тесты:
- `test_config.py`: загрузка, мерж, валидация конфигов
- `test_retention.py`: логика retention policy, определение пакетов для удаления
- `test_aptly.py`: моки команд aptly, проверка правильных вызовов
- `test_utils.py`: парсинг версий, метаданные

Использовать pytest, mock для subprocess.

#### Шаг 6.2: Documentation
**Статус**: Pending
**Зависимости**: все команды реализованы (Фаза 4)
**Можно выполнять параллельно**: с Шагом 6.1

Написать документацию:
- **README.md**: Quick start, установка, примеры использования
- **ARCHITECTURE.md**: архитектурные решения, структура aptly roots
- **CONFIG.md**: детальное описание всех параметров конфигурации
- **WORKFLOWS.md**: описание GitHub Actions, настройка secrets
- **DEVELOPMENT.md**: для разработчиков, запуск тестов

---

## Диаграмма зависимостей

```
Фаза 1 (все параллельно)
├── 1.1 Структура проекта
├── 1.2 Конфигурация
└── 1.3 Dependencies

Фаза 2 (частично параллельно)
├── 2.1 Config module ← 1.3
├── 2.2 Utils module (независим)
└── 2.3 Aptly wrapper ← 2.1

Фаза 3 (параллельно)
├── 3.1 Retention logic ← 2.1, 2.2
└── 3.2 GPG integration ← 2.1

Фаза 4 (последовательно от 4.1, затем параллельно)
├── 4.1 CLI core ← 2.1
├── 4.2 Add command ← 4.1, 2.3, 3.2
├── 4.3 Repo management ← 4.1, 2.3, 3.2
└── 4.4 Cleanup command ← 4.1, 2.3, 3.1

Фаза 5 (параллельно)
├── 5.1 Add workflow ← 4.2
├── 5.2 Cleanup workflow ← 4.4
└── 5.3 Create workflow ← 4.3

Фаза 6 (параллельно)
├── 6.1 Unit tests ← 3.1, 2.1, 2.3
└── 6.2 Documentation ← Фаза 4
```

## Приоритеты реализации

### Критический путь (MVP):
1. Фаза 1 → Фаза 2 → Фаза 4.1 → Фаза 4.2 → Фаза 5.1

Этого достаточно для базового добавления пакетов через GitHub Actions.

### Полная функциональность:
Все фазы в указанном порядке с учетом зависимостей.

### Можно отложить на потом:
- Retention/cleanup (Фаза 3.1, 4.4, 5.2) - если изначально планируется ручное управление
- Тесты (Фаза 6.1) - хотя лучше писать параллельно с кодом

## Оценка времени

- Фаза 1: 1-2 часа
- Фаза 2: 4-6 часов
- Фаза 3: 3-4 часа
- Фаза 4: 6-8 часов
- Фаза 5: 3-4 часа
- Фаза 6: 4-6 часов

**Общая оценка**: 21-30 часов работы

**MVP (критический путь)**: 12-16 часов

