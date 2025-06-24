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
- Предусмотрена отказоустойчивость
- Масштабирование достигается путем увеличения количества воркеров

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

2. Создайте файл `.env` с переменными окружения (необязательно, в config.py всё указано):
   ```
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=task_manager
   POSTGRES_HOST=localhost
   RABBITMQ_DEFAULT_USER=guest
   RABBITMQ_DEFAULT_PASS=guest
   RABBITMQ_PORT=5672
   RABBITMQ_VHOST=/
   TASK_CONCURRENCY=4
   ```

3. Запустите проект с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. API будет доступно по адресу: http://localhost:8000
5. Мониторинг будет доступен по адресу: http://localhost:8000/monitor/dashboard
6. RabbitMQ: http://localhost:15672/ (Username: guest Password: guest)

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

## Postman коллекция

В репозитории есть файл `TaskManager.postman_collection.json`, который содержит коллекцию запросов для Postman. Импортируйте его в Postman для удобного тестирования API. 