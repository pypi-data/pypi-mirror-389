# Debian Repository Manager

Система управления набором Debian-like репозиториев для множественных дистрибутивов, архитектур и коллекций с поддержкой атомарных обновлений и GitHub Actions интеграции.

## Возможности

- 🚀 **Атомарные обновления** через aptly snapshots
- 🔄 **Multi-codename**: bookworm, noble, trixie, jammy и др.
- 🏗️ **Multi-architecture**: amd64, arm64, riscv64
- 📦 **Multi-component**: различные коллекции пакетов
- 🔐 **GPG подпись** всех репозиториев
- 🧹 **Retention policies**: автоматическая очистка старых версий
- 🤖 **GitHub Actions**: интеграция в CI/CD pipeline
- 🔍 **Верификация**: проверка консистентности репозиториев

## Архитектура

Система построена на базе [aptly](https://www.aptly.info/) с использованием:
- Изоляции через multi-root (отдельный aptly root для каждого codename)
- Snapshots для атомарности операций
- Python CLI для удобного управления
- GitHub Actions для автоматизации

См. [ARCHITECTURE.md](docs/ARCHITECTURE.md) для детального описания.

## Требования

### На сервере
- aptly >= 1.5.0
- gpg (GnuPG) >= 2.2
- Python >= 3.11
- rsync (для GitHub Actions)
- SSH сервер (для GitHub Actions)

### Для разработки
- Python >= 3.11 (tested on 3.11, 3.12, 3.13)
- pip
- virtualenv (рекомендуется)
- Docker (для integration тестов)

## Установка

### На сервере

```bash
# Установка aptly
wget -qO - https://www.aptly.info/pubkey.txt | gpg --dearmor > /etc/apt/trusted.gpg.d/aptly.gpg
echo "deb http://repo.aptly.info/ squeeze main" > /etc/apt/sources.list.d/aptly.list
apt update
apt install aptly

# Клонирование репозитория
git clone https://github.com/jethome/repomanager.git /opt/repomanager
cd /opt/repomanager

# Установка Python зависимостей
pip3 install -e .

# Или установка через setup.py
python3 setup.py install

# Создание конфигурации
cp config.yaml.example /etc/repomanager/config.yaml
vim /etc/repomanager/config.yaml

# Импорт GPG ключа (если еще не импортирован)
gpg --import /path/to/private-key.asc

# Настройка gpg-agent для кеширования passphrase
mkdir -p ~/.gnupg
cat >> ~/.gnupg/gpg-agent.conf <<EOF
default-cache-ttl 28800
max-cache-ttl 28800
EOF
gpg-connect-agent reloadagent /bye
```

### Для разработки

```bash
git clone https://github.com/jethome/repomanager.git
cd repomanager

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Установка в режиме разработки
pip install -e .

# Запуск тестов
pytest
```

## Конфигурация

Основной файл конфигурации: `config.yaml`

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
    jethome-armbian:
      min_versions: 3
      max_age_days: 60

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

См. `config.yaml.example` для всех доступных опций.

## Использование

### CLI команды

#### Добавление пакетов

```bash
# Добавить отдельные пакеты
repomanager add --codename bookworm --component jethome-tools \
    --packages package1.deb package2.deb

# Добавить все пакеты из директории (рекурсивно)
repomanager add --codename bookworm --component jethome-tools \
    --package-dir /path/to/packages/

# С указанием конфига
repomanager --config /etc/repomanager/config.yaml add \
    --codename noble --component jethome-armbian \
    --package-dir /tmp/armbian-packages/
```

#### Создание репозитория

```bash
# Создать новый репозиторий
repomanager create-repo --codename trixie --component jethome-tools

# Репозиторий будет доступен по адресу:
# http://repo.jethome.ru/trixie/jethome-tools
```

#### Удаление репозитория

```bash
# Удалить репозиторий (требует подтверждения)
repomanager delete-repo --codename noble --component old-component --confirm
```

#### Просмотр репозиториев

```bash
# Список всех репозиториев
repomanager list

# Репозитории для конкретного codename
repomanager list --codename bookworm

# Пакеты в конкретном компоненте
repomanager list --codename bookworm --component jethome-tools
```

#### Очистка старых пакетов

```bash
# Dry-run (показать что будет удалено)
repomanager cleanup --codename bookworm --component jethome-tools --dry-run

# Применить очистку
repomanager cleanup --codename bookworm --component jethome-tools --apply

# Очистить все репозитории
repomanager cleanup --apply
```

#### Верификация

```bash
# Проверить консистентность репозитория
repomanager verify --codename bookworm --component jethome-tools

# Проверить все репозитории
repomanager verify
```

### GitHub Actions

Для использования в CI/CD необходимо настроить GitHub Secrets:

#### Секреты

- `SSH_PRIVATE_KEY`: SSH ключ для доступа к серверу
- `SSH_HOST`: адрес сервера (например, repo.jethome.ru)
- `SSH_USER`: пользователь для SSH (например, repomanager)
- `GPG_PRIVATE_KEY`: GPG приватный ключ (base64 encoded)
- `GPG_PASSPHRASE`: пароль от GPG ключа
- `GPG_KEY_ID`: ID GPG ключа

#### Пример использования в workflow

```yaml
name: Build and Publish Packages

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build packages
        run: |
          # ваш процесс сборки пакетов
          ./build-packages.sh

      - name: Upload packages
        uses: actions/upload-artifact@v3
        with:
          name: packages
          path: output/*.deb

  publish:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          repository: jethome/repomanager

      - name: Add packages to repository
        uses: ./.github/workflows/add-packages.yml
        with:
          codename: bookworm
          component: jethome-tools
          artifact_name: packages
```

См. [WORKFLOWS.md](docs/WORKFLOWS.md) для детального описания GitHub Actions.

## Структура URL

Репозитории доступны по следующей схеме:
```
http://repo.jethome.ru/{codename}/{component}
```

### Примеры

```
http://repo.jethome.ru/bookworm/jethome-tools
http://repo.jethome.ru/bookworm/jethome-armbian
http://repo.jethome.ru/noble/jethome-tools
http://repo.jethome.ru/trixie/jethome-bookworm
```

### Использование в системе

`/etc/apt/sources.list.d/jethome.list`:
```
deb http://repo.jethome.ru/bookworm jethome-tools main
deb http://repo.jethome.ru/bookworm jethome-armbian main
deb http://repo.jethome.ru/bookworm jethome-bookworm main
```

После добавления репозитория:
```bash
# Импорт GPG ключа
wget -qO - http://repo.jethome.ru/pubkey.gpg | gpg --dearmor > /etc/apt/trusted.gpg.d/jethome.gpg

# Обновление
apt update

# Установка пакетов
apt install jethome-package
```

## Retention Policies

Система автоматически управляет хранением старых версий пакетов:

- **min_versions**: минимальное количество версий для сохранения (по умолчанию: 5)
- **max_age_days**: максимальный возраст пакета в днях (по умолчанию: 90)

Логика: всегда сохраняются последние N версий, независимо от возраста. Версии старше M дней удаляются, если их больше чем N.

Настройка в `config.yaml`:
```yaml
retention:
  default:
    min_versions: 5
    max_age_days: 90
  overrides:
    jethome-armbian:  # специфичная политика для компонента
      min_versions: 3
      max_age_days: 60
```

## Troubleshooting

### GPG signing fails

```bash
# Проверить наличие ключа
gpg --list-secret-keys

# Проверить gpg-agent
gpg-connect-agent 'keyinfo --list' /bye

# Перезапустить gpg-agent
gpgconf --kill gpg-agent
gpg-connect-agent /bye
```

### Aptly errors

```bash
# Проверить статус репозиториев
aptly repo list

# Проверить snapshots
aptly snapshot list

# Проверить published
aptly publish list

# Очистить orphaned files
aptly db cleanup
```

### Permissions issues

```bash
# Проверить права
ls -la /srv/aptly/
ls -la /srv/repo/public/

# Исправить права
chown -R repomanager:repomanager /srv/aptly/
chown -R www-data:repomanager /srv/repo/public/
chmod -R g+w /srv/aptly/ /srv/repo/public/
```

## Разработка

### Структура проекта

```
repomanager/
├── repomanager/        # Основной пакет
│   ├── __init__.py
│   ├── cli.py          # CLI interface
│   ├── aptly.py        # Aptly wrapper
│   ├── config.py       # Configuration management
│   ├── retention.py    # Retention policy logic
│   ├── gpg.py          # GPG operations
│   └── utils.py        # Utilities
├── tests/              # Тесты
├── .github/workflows/  # GitHub Actions
├── config.yaml.example # Пример конфигурации
└── setup.py            # Установка
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=repomanager --cov-report=html

# Конкретный модуль
pytest tests/test_retention.py

# Verbose
pytest -v
```

### Code style

Проект использует:
- **Black** для форматирования (spaces, не tabs)
- **flake8** для линтинга
- **mypy** для type checking

```bash
# Форматирование
black repomanager/

# Линтинг
flake8 repomanager/

# Type checking
mypy repomanager/
```

## Документация

### Для пользователей
- [QUICKSTART.md](docs/QUICKSTART.md) - быстрый старт за 5 минут
- [APT_CONFIGURATION.md](docs/APT_CONFIGURATION.md) - настройка APT для всех систем

### Для администраторов
- [CONFIG.md](docs/CONFIG.md) - детальное описание конфигурации

### Для разработчиков
- [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - финальный план реализации
- [PLAN.md](docs/PLAN.md) - оригинальный план (reference)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - архитектурные решения
- [IMPLEMENTATION_STEPS.md](docs/IMPLEMENTATION_STEPS.md) - пошаговая инструкция реализации
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - руководство для разработчиков
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - структура проекта

## Лицензия

MIT License - см. [LICENSE](LICENSE)

## Авторы

JetHome Team

## Contributing

Pull requests are welcome! Please make sure to:
1. Добавить тесты для новой функциональности
2. Обновить документацию
3. Следовать code style (black, flake8)
4. Проверить что все тесты проходят

