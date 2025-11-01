# Запуск тестов AutoSklad Server

## Общие требования

- **ОС**: Windows 10/11
- **Python**: 3.10–3.12 (x64), добавлен в PATH
- **VS Code**: Установлен с Python расширением
- **Зависимости**: Активированное виртуальное окружение сервера

## Подготовка окружения

### 1. Активация виртуального окружения

```powershell
cd server
.\venv\Scripts\Activate.ps1
```

### 2. Установка зависимостей (если не установлены)

```powershell
pip install -r requirements.txt
```

### 3. Запуск сервера для тестирования

В отдельном терминале VS Code:

```powershell
cd server
.\venv\Scripts\Activate.ps1
python main.py
```

Сервер должен быть доступен по `http://127.0.0.1:8000`

## Запуск тестов

### Вариант 1: Запуск через VS Code Terminal

1. Откройте VS Code в корне проекта
2. Откройте терминал: `Ctrl + Shift + ` `
3. Перейдите в папку тестов:

```powershell
cd server/tests
```

4. Активируйте виртуальное окружение:

```powershell
.\venv\Scripts\Activate.ps1
```

5. Запустите нужный тест:

```powershell
# API connectivity test
python api_connectivity_test.py --url http://127.0.0.1:8000

# Mass load API test
python mass_load_api_test.py --url http://127.0.0.1:8000
```

### Вариант 2: Запуск через VS Code Run/Debug

1. Откройте файл теста в VS Code (например, `server/tests/mass_load_api_test.py`)
2. Нажмите `F5` или откройте Command Palette (`Ctrl+Shift+P`) → "Python: Run Python File in Terminal"
3. VS Code автоматически активирует виртуальное окружение и запустит тест

### Вариант 3: Запуск через PowerShell

```powershell
# Из корня проекта
cd server/tests
.\venv\Scripts\Activate.ps1
python mass_load_api_test.py --url http://127.0.0.1:8000
```

## Доступные тесты

### `api_connectivity_test.py`
- Тестирует базовые API эндпоинты
- Создает группы и инструменты
- Проверяет создание и чтение данных

```powershell
python api_connectivity_test.py --url http://127.0.0.1:8000
```

### `mass_load_api_test.py`
- Тестирует функциональность массовой загрузки
- Создает 5 типов инструментов (40 шт суммарно)
- Выполняет массовую загрузку со случайным распределением по ячейкам
- Сохраняет массовую загрузку

```powershell
python mass_load_api_test.py --url http://127.0.0.1:8000
```

## Параметры командной строки

### Общие параметры

- `--url URL`: URL запущенного сервера (по умолчанию `http://127.0.0.1:8000`)

Примеры:

```powershell
# Тест на локальном сервере
python mass_load_api_test.py

# Тест на удаленном сервере
python mass_load_api_test.py --url http://192.168.1.100:8000
```

## Логирование

Тесты создают лог-файлы в папке `logs/` с временными метками:

- `api_connectivity_test_YYYYMMDD_HHMMSS.txt`
- `mass_load_api_test_YYYYMMDD_HHMMSS.txt`

Логи содержат подробную информацию о каждом шаге тестирования.

## Диагностика проблем

### Ошибка "ModuleNotFoundError: No module named 'requests'"

```powershell
pip install requests
```

### Ошибка подключения к серверу

- Убедитесь, что сервер запущен: `python main.py` в папке server
- Проверьте URL: `curl http://127.0.0.1:8000/docs`
- Проверьте фаервол Windows

### Ошибка аутентификации

- Проверьте учетные данные в тесте (login="1111", password="1111")
- Пересоздайте базу данных сервера если проблемы с пользователями

### Ошибка создания данных

- Очистите тестовые данные: `.\cleanup_databases.ps1`
- Перезапустите сервер для пересоздания БД

## Структура тестов

Тесты наследуются от `ApiConnectivityTest` и реализуют:

1. **Аутентификацию**: Получение JWT токена
2. **Создание тестовых данных**: Группы и инструменты
3. **API вызовы**: GET/POST запросы к эндпоинтам
4. **Валидация**: Проверка успешности операций
5. **Логирование**: Подробные логи выполнения

## Очистка после тестирования

После завершения тестов очистите тестовые данные:

```powershell
# Из корня проекта
.\cleanup_databases.ps1
```

Это удалит все созданные тестовые группы, инструменты и массовые загрузки.
