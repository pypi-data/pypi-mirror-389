# GitHub Actions Workflows

Описание всех GitHub Actions workflows в проекте.

## 🔍 Code Review (`code-review.yml`)

**Триггеры:**
- Pull Request (opened, synchronize, reopened)
- Изменения в Python файлах

**Что делает:**
1. Проверка форматирования (Black)
2. Линтинг (flake8)
3. Type checking (mypy)
4. Запуск тестов с coverage
5. Проверка trailing spaces
6. Security scan (Bandit)
7. Dependency review

**Результат:**
- Автоматический комментарий в PR с результатами проверок
- Список ошибок и рекомендации по исправлению
- Security warnings если есть

**Использование:**
Запускается автоматически при создании/обновлении PR.

---

## 🔧 CI Auto-Fix (`ci-auto-fix.yml`)

**Триггеры:**
- Ручной запуск (workflow_dispatch)
- Комментарий `/fix-ci` в PR

**Что делает:**
1. Применяет Black форматирование
2. Сортирует импорты (isort)
3. Удаляет trailing spaces
4. Коммитит изменения автоматически
5. Предлагает ручные исправления для сложных проблем

**Параметры:**
- `pr_number`: номер PR для исправления (опционально)
- `fix_type`: тип исправлений (all/formatting/imports/trailing-spaces)

**Использование:**

### Из интерфейса GitHub
1. Actions → CI Auto-Fix → Run workflow
2. Выбрать PR и тип исправлений

### Из комментария в PR
Просто напишите комментарий:
```
/fix-ci
```

Workflow автоматически:
- Применит исправления
- Закоммитит изменения
- Напишет отчет в PR

---

## 📚 Documentation Update (`docs-update.yml`)

**Триггеры:**
- Push в main (изменения в Python/docs)
- Pull Request (изменения в Python/docs)
- Ручной запуск для changelog

**Что делает:**
1. **Проверка документации:**
   - Ищет недокументированные модули
   - Ищет недокументированные config опции
   - Проверяет прогресс TODO
   - Ищет битые ссылки

2. **Автообновление (только main):**
   - Обновляет список модулей в PROJECT_STRUCTURE.md
   - Добавляет badges в README
   - Обновляет прогресс в SUMMARY.md

3. **Генерация changelog (manual):**
   - Парсит коммиты по типам (feat/fix/chore)
   - Обновляет CHANGELOG.md

**Параметры (manual):**
- `update_type`: тип обновления (all/api/config/changelog)

**Результат в PR:**
- Комментарий с отчетом о документации
- Список недостающих docs
- Прогресс выполнения

**Использование:**

### Автоматическое
Запускается при каждом push/PR с изменениями.

### Ручное обновление changelog
```
Actions → Documentation Update → Run workflow
Select: changelog
```

---

## ✅ Tests (`tests.yml`)

**Триггеры:**
- Push в main/develop
- Pull Request в main/develop

**Что делает:**

### 1. Test Matrix
Запускает тесты на Python 3.8, 3.9, 3.10, 3.11, 3.12:
- Pytest с coverage
- Upload coverage в Codecov (Python 3.11)
- Генерация coverage badge
- Архив coverage report

### 2. Code Quality
- Black formatting check
- flake8 linting
- mypy type checking
- isort imports check

### 3. Security Scan
- Bandit (security linter)
- Safety (dependency vulnerabilities)
- Upload security reports

### 4. Integration Tests
- Установка aptly
- Запуск integration тестов
- Только для PR и main

### 5. Build Package
- Сборка Python package
- Проверка с twine
- Upload dist artifacts

**Результат:**
- Badge статуса тестов
- Coverage report
- Security reports
- Build artifacts

---

## 📦 Workflows для управления репозиторием

### Add Packages (`add-packages.yml`)

**Статус:** 🚧 Будет создан в Phase 4

**Назначение:**
Добавление пакетов в репозиторий из CI/CD

**Триггеры:**
- workflow_call (reusable)
- workflow_dispatch (manual)

**Параметры:**
- `codename`: bookworm/noble/trixie/jammy
- `component`: jethome-tools/jethome-armbian/etc
- `artifact_name`: имя artifact с пакетами
- `packages_path`: путь к директории с пакетами

**Что делает:**
1. Скачивает artifact с пакетами
2. Setup SSH для доступа к серверу
3. Import GPG ключа
4. rsync пакетов на сервер
5. SSH execute `debdebrepomanager add`
6. Cleanup (удаление временных файлов и GPG ключа)
7. Report в GitHub Actions summary

---

### Cleanup Repository (`cleanup-repo.yml`)

**Статус:** 🚧 Будет создан в Phase 4

**Назначение:**
Периодическая очистка старых пакетов по retention policy

**Триггеры:**
- schedule (weekly: Sunday 2 AM)
- workflow_dispatch (manual)

**Параметры:**
- `codename`: конкретный codename или all
- `component`: конкретный component или all
- `dry_run`: preview без удаления (default: false)

**Что делает:**
1. Setup SSH
2. SSH execute `debrepomanager cleanup`
3. Collect report
4. Post report в Issue/Comment (опционально)

---

### Create Repository (`create-repo.yml`)

**Статус:** 🚧 Будет создан в Phase 4

**Назначение:**
Создание нового репозитория

**Триггеры:**
- workflow_dispatch (manual)

**Параметры:**
- `codename`: bookworm/noble/trixie/jammy
- `component`: название компонента

**Что делает:**
1. Setup SSH и GPG
2. SSH execute `debdebrepomanager create-repo`
3. Verify creation
4. Report результата

---

## 🔐 Required Secrets

Для работы workflows с удаленным сервером нужны следующие secrets:

### SSH Access
- `SSH_PRIVATE_KEY`: SSH приватный ключ для доступа к серверу
- `SSH_HOST`: адрес сервера (например, repo.jethome.ru)
- `SSH_USER`: пользователь SSH (например, repomanager)

### GPG Signing
- `GPG_PRIVATE_KEY`: GPG приватный ключ (base64 encoded)
  ```bash
  cat key.asc | base64 -w0
  ```
- `GPG_PASSPHRASE`: пароль от GPG ключа
- `GPG_KEY_ID`: ID GPG ключа

### Optional
- `CODECOV_TOKEN`: токен для Codecov (для coverage reports)

## 📋 Настройка Secrets

1. GitHub Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Добавить каждый secret из списка выше

## 🎯 Использование в других репозиториях

### Пример: Автоматическая публикация пакетов

`.github/workflows/build-and-publish.yml` в вашем репозитории:

```yaml
name: Build and Publish Packages

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build packages
        run: |
          # Ваш процесс сборки
          ./build.sh

      - name: Upload packages
        uses: actions/upload-artifact@v4
        with:
          name: debian-packages
          path: output/*.deb

  publish:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: jethome/repomanager
          path: repomanager

      - name: Download packages
        uses: actions/download-artifact@v4
        with:
          name: debian-packages
          path: ./packages

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Transfer and add packages
        run: |
          TEMP_DIR="/tmp/packages-${{ github.run_id }}"
          rsync -avz ./packages/ \
            ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }}:$TEMP_DIR/

          ssh ${{ secrets.SSH_USER }}@${{ secrets.SSH_HOST }} \
            "debrepomanager add \
              --codename bookworm \
              --component jethome-tools \
              --package-dir $TEMP_DIR && \
             rm -rf $TEMP_DIR"
```

## 🔄 Workflow Dependencies

```
code-review.yml (на каждый PR)
    ↓
ci-auto-fix.yml (если нужно)
    ↓
tests.yml (полное тестирование)
    ↓
docs-update.yml (проверка документации)
```

## 📊 Статус Badges

Добавьте в README.md:

```markdown
![Tests](https://github.com/jethome/repomanager/workflows/Tests/badge.svg)
![Code Review](https://github.com/jethome/repomanager/workflows/Code%20Review/badge.svg)
![Coverage](https://codecov.io/gh/jethome/repomanager/branch/main/graph/badge.svg)
```

## 🛠️ Отладка Workflows

### Просмотр логов
1. Actions tab в GitHub
2. Выбрать workflow run
3. Раскрыть step для просмотра логов

### Re-run failed jobs
1. Открыть failed workflow run
2. Click "Re-run jobs" → "Re-run failed jobs"

### Ручной запуск с debug
1. Actions → выбрать workflow
2. Run workflow
3. В actions logs будет полный output

### Локальное тестирование
Используйте [act](https://github.com/nektos/act) для локального запуска workflows:

```bash
# Установка act
brew install act  # macOS
# или
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Запуск workflow локально
act pull_request -W .github/workflows/code-review.yml

# С секретами
act -s GITHUB_TOKEN=your_token
```

## 📝 Best Practices

1. **Всегда используйте `continue-on-error: true`** для non-critical checks
2. **Кешируйте зависимости** (`cache: 'pip'` в setup-python)
3. **Используйте matrix** для тестирования на разных версиях
4. **Добавляйте `if: always()`** для cleanup steps
5. **Ограничивайте permissions** до минимально необходимых
6. **Используйте artifacts** для передачи файлов между jobs
7. **Добавляйте timeout** для долгих операций

## 🔗 Полезные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
- [Act - Local Testing](https://github.com/nektos/act)

---

**Обновлено:** 2025-10-29



