# Task Manager

Асинхронный сервис управления задачами с использованием FastAPI, SQLAlchemy, RabbitMQ и asyncio.

## Функциональность

- Создание, чтение, обновление и удаление задач
- Асинхронное выполнение задач с использованием RabbitMQ
- Приоритизация задач (LOW, MEDIUM, HIGH)
- Отслеживание статусов задач (NEW, PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED)
- Отмена выполняющихся задач
- Мониторинг выполнения задач через веб-интерфейс
- API для получения статистики по задачам

## Технологии

- **FastAPI**: Асинхронный веб-фреймворк для создания API
- **SQLAlchemy**: ORM для работы с базой данных
- **RabbitMQ**: Брокер сообщений для асинхронного выполнения задач
- **PostgreSQL**: База данных для хранения задач и их статусов
- **aio-pika**: Асинхронная библиотека для работы с RabbitMQ
- **asyncpg**: Асинхронный драйвер для PostgreSQL
- **Chart.js**: Библиотека для визуализации данных в мониторинге
- **Tailwind CSS**: Фреймворк для стилизации веб-интерфейса

## Структура проекта

```
TaskManager/
  ├── app/
  │   ├── database/          # Настройка подключения к базе данных
  │   ├── models/            # Модели SQLAlchemy
  │   ├── routers/           # Маршруты FastAPI
  │   ├── schemas/           # Pydantic-схемы для валидации данных
  │   ├── services/          # Бизнес-логика
  │   ├── tasks.py           # Обработчики задач
  │   ├── worker.py          # Воркер для обработки задач из RabbitMQ
  │   ├── monitoring.py      # Мониторинг задач
  │   └── templates/         # HTML-шаблоны для мониторинга
  ├── docker-compose.yml     # Настройка Docker Compose
  ├── Dockerfile             # Настройка Docker
  ├── main.py                # Точка входа в приложение
  ├── requirements.txt       # Зависимости проекта
  └── tests/                 # Тесты
```

## Запуск проекта

### С использованием Docker Compose

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Goshansky/TaskManager.git
   cd TaskManager
   ```

2. Создайте файл `.env` с переменными окружения:
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=taskmanager
   POSTGRES_HOST=db
   RABBITMQ_DEFAULT_USER=guest
   RABBITMQ_DEFAULT_PASS=guest
   ```

3. Запустите проект с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. API будет доступно по адресу: http://localhost:8000
5. Мониторинг будет доступен по адресу: http://localhost:8000/monitor/dashboard

### Без Docker

1. Установите и настройте PostgreSQL и RabbitMQ
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` с переменными окружения:
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=taskmanager
   POSTGRES_HOST=localhost
   RABBITMQ_DEFAULT_USER=guest
   RABBITMQ_DEFAULT_PASS=guest
   ```

4. Запустите API-сервер:
   ```bash
   uvicorn main:app --reload
   ```

5. Запустите воркер в отдельном терминале:
   ```bash
   python worker.py
   ```

## API Endpoints

### Задачи

- `POST /tasks/` - Создать новую задачу
- `POST /tasks/broken` - Создать задачу, которая завершится с ошибкой (для тестирования)
- `GET /tasks/` - Получить список задач с возможностью фильтрации по статусу и приоритету
- `GET /tasks/{task_id}` - Получить информацию о конкретной задаче
- `PUT /tasks/{task_id}` - Обновить задачу
- `DELETE /tasks/{task_id}` - Удалить задачу
- `POST /tasks/{task_id}/cancel` - Отменить выполнение задачи

### Мониторинг

- `GET /monitor/dashboard` - Веб-интерфейс для мониторинга задач
- `GET /monitor/stats` - API для получения статистики по задачам

## Тестирование

Для запуска тестов выполните:

```bash
pytest
```

## Postman коллекция

В репозитории есть файл `TaskManager.postman_collection.json`, который содержит коллекцию запросов для Postman. Импортируйте его в Postman для удобного тестирования API. 