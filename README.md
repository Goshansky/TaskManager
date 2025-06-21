# Task Manager API

Асинхронный сервис для управления задачами с возможностью масштабирования и отказоустойчивости.

## Функциональные возможности

### Основные возможности
1. Создание задач через REST API
2. Асинхронная обработка задач в фоновом режиме
3. Параллельная обработка нескольких задач
4. Система приоритетов для задач
5. Создание заведомо сломанных задач для тестирования
6. Создание задач с повторными попытками выполнения

### Статусная модель задач
1. NEW - новая задача
2. PENDING - ожидает обработки
3. IN_PROGRESS - в процессе выполнения
4. COMPLETED - завершено успешно
5. FAILED - завершено с ошибкой
6. CANCELLED - отменено

### Атрибуты задач
1. Уникальный идентификатор
2. Название
3. Описание
4. Приоритет (LOW, MEDIUM, HIGH)
5. Статус
6. Время создания
7. Время начала выполнения
8. Время завершения
9. Результат выполнения
10. Информация об ошибках (если есть)

## Технологический стек

- FastAPI - REST API фреймворк
- Celery - асинхронная обработка задач
- Redis - брокер сообщений и хранилище результатов
- PostgreSQL - база данных
- Docker - контейнеризация
- Flower - мониторинг задач Celery

## Запуск проекта

### С использованием Docker

```bash
docker-compose up -d
```

Сервисы будут доступны по следующим адресам:
- API: http://localhost:8000
- Flower (мониторинг задач): http://localhost:5555

### Локальный запуск (без Docker)

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите Redis:
```bash
# Установите Redis и запустите сервер
```

3. Запустите PostgreSQL:
```bash
# Установите PostgreSQL и создайте базу данных task_manager
```

4. Запустите API сервер:
```bash
uvicorn main:app --reload
```

5. Запустите Celery worker:
```bash
celery -A app.worker.celery worker --loglevel=info
```

6. Запустите Flower для мониторинга:
```bash
celery -A app.worker.celery flower --port=5555
```

## API Endpoints

### Задачи

- **GET /tasks/** - Получение списка всех задач
- **GET /tasks/{task_id}** - Получение задачи по ID
- **POST /tasks/** - Создание новой задачи
- **POST /tasks/broken** - Создание заведомо сломанной задачи
- **POST /tasks/retry** - Создание задачи с повторными попытками
- **PUT /tasks/{task_id}** - Обновление задачи (только title, description и priority)
- **DELETE /tasks/{task_id}** - Удаление задачи
- **POST /tasks/{task_id}/cancel** - Отмена выполнения задачи

## Примеры использования API

### Создание новой задачи

```bash
curl -X POST "http://localhost:8000/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тестовая задача",
    "description": "Описание тестовой задачи",
    "priority": "HIGH"
  }'
```

### Получение списка задач

```bash
curl -X GET "http://localhost:8000/tasks/"
```

### Отмена задачи

```bash
curl -X POST "http://localhost:8000/tasks/1/cancel"
```

## Мониторинг

Для мониторинга задач используйте Flower, доступный по адресу http://localhost:5555 

## Тестирование

Для тестирования API можно использовать Postman коллекцию `TaskManager.postman_collection.json`. 