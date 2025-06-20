# API Управления Задачами

Сервис для управления задачами на базе FastAPI с использованием PostgreSQL.

## Возможности

- Создание, чтение, обновление и удаление задач
- Отслеживание статуса задач (NEW, PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED)
- Приоритизация задач (LOW, MEDIUM, HIGH)
- Автоматическое отслеживание временных меток жизненного цикла задачи

## Требования

- Python 3.8+
- Docker и Docker Compose

## Установка и запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Goshansky/TaskManager.git
cd TaskManager
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Запустите базу данных PostgreSQL с помощью Docker:

```bash
docker-compose up -d
```

4. Запустите приложение:

```bash
uvicorn main:app --reload
```

5. Доступ к документации API:

Откройте браузер и перейдите по адресу [http://localhost:8000/docs](http://localhost:8000/docs)

## Конечные точки API

- `GET /tasks/` - Получение списка всех задач (с возможностью фильтрации по статусу и приоритету)
- `POST /tasks/` - Создание новой задачи
- `GET /tasks/{task_id}` - Получение конкретной задачи по ID
- `PUT /tasks/{task_id}` - Обновление задачи
- `DELETE /tasks/{task_id}` - Удаление задачи

## Жизненный цикл статусов задачи

1. NEW - Начальное состояние для вновь созданных задач
2. PENDING - Задача ожидает обработки
3. IN_PROGRESS - Задача в процессе выполнения
4. COMPLETED - Задача успешно завершена
5. FAILED - Выполнение задачи завершилось с ошибкой
6. CANCELLED - Задача была отменена

## Структура проекта

```
TaskManager/
├── app/
│   ├── database/      # Модули для работы с базой данных
│   ├── models/        # SQLAlchemy модели
│   ├── routers/       # FastAPI роутеры
│   ├── schemas/       # Pydantic схемы
│   └── services/      # Бизнес-логика и CRUD операции
├── docker-compose.yml # Конфигурация Docker для PostgreSQL
├── main.py            # Точка входа в приложение
└── requirements.txt   # Зависимости проекта
```

## Тестирование API

В репозитории есть файл `TaskManager.postman_collection.json`, который можно импортировать в Postman для тестирования API. Коллекция содержит все необходимые запросы для работы с задачами. 