# Configuration Reference

Полное описание всех параметров конфигурации Debian Repository Manager.

## Файлы конфигурации

### Приоритет загрузки

1. **Аргументы командной строки** (высший приоритет)
2. **Серверная конфигурация**: `/etc/repomanager/config.yaml`
3. **Конфигурация из репозитория**: `./config.yaml`
4. **Значения по умолчанию** (низший приоритет)

### Расположение файлов

- **В репозитории**: `config.yaml` (для defaults и shared настроек)
- **На сервере**: `/etc/repomanager/config.yaml` (для server-specific настроек и секретов)
- **Пример**: `config.yaml.example` (шаблон с описанием всех опций)

## Структура конфигурации

### GPG

Настройки GPG подписи репозиториев.

```yaml
gpg:
  key_id: "1234567890ABCDEF"
  use_agent: true
  gpg_path: "/usr/bin/gpg"
```

#### `gpg.key_id` (обязательный)
- **Тип**: string
- **Описание**: ID GPG ключа для подписи репозиториев
- **Пример**: `"1234567890ABCDEF"` или `"user@example.com"`
- **Как получить**: `gpg --list-keys` (последние 16 символов)

#### `gpg.use_agent` (опциональный)
- **Тип**: boolean
- **По умолчанию**: `true`
- **Описание**: Использовать gpg-agent для кеширования passphrase
- **Рекомендация**: `true` для серверного использования, `false` для CI/CD

#### `gpg.gpg_path` (опциональный)
- **Тип**: string
- **По умолчанию**: автоопределение через `which gpg`
- **Описание**: Путь к исполняемому файлу gpg
- **Пример**: `"/usr/bin/gpg2"`

---

### Aptly

Настройки путей и конфигурации aptly.

```yaml
aptly:
  root_base: "/srv/aptly"
  publish_base: "/srv/repo/public"
  aptly_path: "/usr/bin/aptly"
```

#### `aptly.root_base` (обязательный)
- **Тип**: string
- **Описание**: Базовая директория для aptly roots
- **Структура**: Для каждого codename создается поддиректория:
  ```
  /srv/aptly/
    ├── bookworm/
    ├── noble/
    └── trixie/
  ```
- **Права доступа**: должна быть доступна для записи пользователю repomanager
- **Пример**: `"/srv/aptly"`, `"/var/lib/aptly"`

#### `aptly.publish_base` (обязательный)
- **Тип**: string
- **Описание**: Базовая директория для published репозиториев (веб-сервер root)
- **Структура**:
  ```
  /srv/repo/public/
    ├── bookworm/
    │   ├── jethome-tools/
    │   └── jethome-armbian/
    └── noble/
        └── jethome-tools/
  ```
- **Права доступа**: должна быть доступна для чтения веб-серверу (www-data)
- **Пример**: `"/srv/repo/public"`, `"/var/www/repo"`

#### `aptly.aptly_path` (опциональный)
- **Тип**: string
- **По умолчанию**: автоопределение через `which aptly`
- **Описание**: Путь к исполняемому файлу aptly
- **Пример**: `"/usr/local/bin/aptly"`

---

### Retention

Политики хранения старых версий пакетов.

```yaml
retention:
  default:
    min_versions: 5
    max_age_days: 90
  overrides:
    jethome-armbian:
      min_versions: 3
      max_age_days: 60
```

#### `retention.default` (обязательный)
Политика по умолчанию для всех компонентов.

##### `retention.default.min_versions`
- **Тип**: integer
- **По умолчанию**: `5`
- **Описание**: Минимальное количество версий пакета для сохранения (независимо от возраста)
- **Логика**: Всегда сохраняются последние N версий, даже если они старше `max_age_days`
- **Рекомендация**: 3-10 в зависимости от частоты релизов

##### `retention.default.max_age_days`
- **Тип**: integer
- **По умолчанию**: `90`
- **Описание**: Максимальный возраст пакета в днях
- **Логика**: Пакеты старше этого срока удаляются, если их больше чем `min_versions`
- **Рекомендация**: 30-180 дней

#### `retention.overrides` (опциональный)
Специфичные политики для отдельных компонентов.

- **Тип**: dict[component_name -> policy]
- **Описание**: Переопределения политики для конкретных компонентов
- **Пример**:
  ```yaml
  overrides:
    jethome-armbian:  # Меньше версий для зеркала armbian
      min_versions: 3
      max_age_days: 60
    jethome-debug:    # Более агрессивная очистка для debug пакетов
      min_versions: 2
      max_age_days: 30
    jethome-lts:      # Дольше храним LTS пакеты
      min_versions: 10
      max_age_days: 365
  ```

---

### Repositories

Конфигурация репозиториев.

```yaml
repositories:
  codenames:
    - bookworm
    - noble
    - trixie
    - jammy
  components:
    - jethome-tools
    - jethome-armbian
    - jethome-bookworm
  architectures:
    - amd64
    - arm64
    - riscv64
  auto_create: true
```

#### `repositories.codenames` (обязательный)
- **Тип**: list[string]
- **Описание**: Список поддерживаемых codenames (Debian/Ubuntu релизов)
- **Debian**: bookworm (12), trixie (13), bullseye (11)
- **Ubuntu**: noble (24.04), jammy (22.04), focal (20.04)
- **Пример**:
  ```yaml
  codenames:
    - bookworm  # Debian 12
    - trixie    # Debian 13
    - noble     # Ubuntu 24.04 LTS
    - jammy     # Ubuntu 22.04 LTS
  ```

#### `repositories.components` (обязательный)
- **Тип**: list[string]
- **Описание**: Список компонентов (коллекций пакетов)
- **Назначение**: Группировка пакетов по функциональности
- **Пример**:
  ```yaml
  components:
    - jethome-tools      # Общие утилиты
    - jethome-armbian    # Armbian support пакеты
    - jethome-bookworm   # BSP пакеты для устройств
  ```

#### `repositories.architectures` (обязательный)
- **Тип**: list[string]
- **Описание**: Список поддерживаемых архитектур
- **Стандартные значения**: amd64, arm64, armhf, i386, riscv64, ppc64el
- **Пример**:
  ```yaml
  architectures:
    - amd64    # x86_64
    - arm64    # ARMv8
    - riscv64  # RISC-V 64-bit
  ```

#### `repositories.auto_create` (опциональный)
- **Тип**: boolean
- **По умолчанию**: `true`
- **Описание**: Автоматически создавать репозиторий при добавлении пакетов
- **Логика**:
  - `true`: Если репозиторий не существует, создается автоматически
  - `false`: При попытке добавить пакеты в несуществующий репозиторий - ошибка
- **Рекомендация**: `true` для CI/CD, `false` для production с ручным управлением

---

### Logging

Настройки логирования.

```yaml
logging:
  level: "INFO"
  file: "/var/log/repomanager/repomanager.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### `logging.level` (опциональный)
- **Тип**: string
- **По умолчанию**: `"INFO"`
- **Допустимые значения**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Описание**: Уровень детализации логов
- **Рекомендация**:
  - `DEBUG`: для разработки и отладки
  - `INFO`: для production
  - `WARNING`: для минимального логирования

#### `logging.file` (опциональный)
- **Тип**: string
- **По умолчанию**: `null` (логи только в stdout)
- **Описание**: Путь к файлу логов
- **Пример**: `"/var/log/repomanager/repomanager.log"`
- **Права доступа**: директория должна существовать и быть доступна для записи

#### `logging.format` (опциональный)
- **Тип**: string
- **По умолчанию**: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- **Описание**: Формат строки лога (Python logging format)
- **Пример**: `"[%(levelname)s] %(message)s"` (упрощенный)

---

### Advanced

Расширенные настройки.

```yaml
advanced:
  max_snapshots: 10
  snapshot_format: "{component}-{codename}-%Y%m%d-%H%M%S"
  parallel: false
  cleanup_dry_run_default: true
```

#### `advanced.max_snapshots` (опциональный)
- **Тип**: integer
- **По умолчанию**: `10`
- **Описание**: Максимальное количество snapshots на компонент
- **Логика**: При превышении лимита старые snapshots удаляются автоматически
- **Рекомендация**: 5-20 (баланс между историей и местом на диске)

#### `advanced.snapshot_format` (опциональный)
- **Тип**: string (strftime format)
- **По умолчанию**: `"{component}-{codename}-%Y%m%d-%H%M%S"`
- **Описание**: Формат имени snapshot'а
- **Плейсхолдеры**:
  - `{component}`: название компонента
  - `{codename}`: codename дистрибутива
  - strftime форматы: `%Y`, `%m`, `%d`, `%H`, `%M`, `%S`
- **Пример**: `"jethome-tools-bookworm-20251029-143022"`

#### `advanced.parallel` (опциональный)
- **Тип**: boolean
- **По умолчанию**: `false`
- **Описание**: Включить параллельную обработку репозиториев
- **Статус**: Зарезервировано для будущего, пока не реализовано

#### `advanced.cleanup_dry_run_default` (опциональный)
- **Тип**: boolean
- **По умолчанию**: `true`
- **Описание**: Dry-run режим по умолчанию для cleanup операций
- **Безопасность**: `true` предотвращает случайное удаление пакетов

---

## Примеры конфигураций

### Минимальная конфигурация

```yaml
gpg:
  key_id: "YOUR_KEY_ID"

aptly:
  root_base: "/srv/aptly"
  publish_base: "/srv/repo/public"

repositories:
  codenames: [bookworm]
  components: [main]
  architectures: [amd64]
```

### Production конфигурация

```yaml
gpg:
  key_id: "1234567890ABCDEF"
  use_agent: true

aptly:
  root_base: "/srv/aptly"
  publish_base: "/srv/repo/public"

retention:
  default:
    min_versions: 5
    max_age_days: 90
  overrides:
    jethome-lts:
      min_versions: 10
      max_age_days: 365
    jethome-testing:
      min_versions: 2
      max_age_days: 14

repositories:
  codenames:
    - bookworm
    - trixie
    - noble
    - jammy
  components:
    - jethome-tools
    - jethome-armbian
    - jethome-lts
    - jethome-testing
  architectures:
    - amd64
    - arm64
    - riscv64
  auto_create: false

logging:
  level: "INFO"
  file: "/var/log/repomanager/repomanager.log"

advanced:
  max_snapshots: 15
  cleanup_dry_run_default: true
```

### Development конфигурация

```yaml
gpg:
  key_id: "DEV_KEY_ID"
  use_agent: true

aptly:
  root_base: "/tmp/test-aptly"
  publish_base: "/tmp/test-repo"

retention:
  default:
    min_versions: 2
    max_age_days: 7

repositories:
  codenames: [bookworm]
  components: [test]
  architectures: [amd64]
  auto_create: true

logging:
  level: "DEBUG"
```

---

## Переменные окружения

Некоторые параметры можно переопределить через переменные окружения:

- `REPOMANAGER_CONFIG`: путь к конфигурационному файлу
- `REPOMANAGER_LOG_LEVEL`: уровень логирования
- `GPG_TTY`: для корректной работы gpg-agent (должна быть установлена в `$(tty)`)

**Пример**:
```bash
export REPOMANAGER_CONFIG=/custom/path/config.yaml
export REPOMANAGER_LOG_LEVEL=DEBUG
export GPG_TTY=$(tty)

debrepomanager list
```

---

## Валидация конфигурации

Проверить корректность конфигурации:

```bash
repomanager --config config.yaml validate
```

Возможные ошибки:
- Отсутствие обязательных параметров
- Некорректные пути (не существуют или нет прав доступа)
- Недоступность GPG ключа
- Неустановленный aptly

---

## См. также

- [README.md](README.md) - общее описание и quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) - архитектура системы
- [config.yaml.example](config.yaml.example) - шаблон конфигурации с комментариями

