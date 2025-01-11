### Примеры тестов приложения на FastAPI с использованием PostgreSQL, pytest и pytest_asyncio

Для тестирования приложения на FastAPI, которое взаимодействует с базой данных PostgreSQL, можно использовать библиотеки `pytest` и `pytest_asyncio`. Ниже приведены примеры того, как можно организовать тесты, управляя сессией базы данных.

#### Структура проекта

Предположим, у вас есть следующая структура проекта:

```
/my_fastapi_app
│
├── app
│   ├── main.py          # Основной файл приложения
│   ├── models.py        # Модели SQLAlchemy
│   └── database.py      # Настройки базы данных
│
├── tests
│   ├── conftest.py      # Настройки тестирования
│   └── test_main.py     # Тесты для приложения
│
└── requirements.txt      # Зависимости проекта
```

### Настройка базы данных и сессий

В файле `app/database.py` вы можете настроить подключение к базе данных и сессии:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
```

### Файл `tests/conftest.py`

В этом файле мы создадим фикстуры для управления сессиями базы данных и клиентом FastAPI:

```python
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi import FastAPI

from app.main import app  # Импортируем приложение FastAPI
from app.database import engine, SessionLocal  # Импортируем настройки базы данных

@pytest.fixture(scope="session")
def event_loop():
    """Создаем новый цикл событий для асинхронных тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Создаем новую сессию базы данных для каждого теста."""
    async with SessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient:
    """Создаем асинхронного клиента для тестирования API."""
    app.dependency_overrides[get_db] = lambda: db_session  # Переопределяем зависимость получения сессии
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(db_session: AsyncSession):
    """Настраиваем базу данных перед каждым тестом."""
    # Здесь можно создать таблицы или заполнить их начальными данными.
    await db_session.commit()  # Подтверждаем изменения в базе данных.
```

### Пример тестов в `tests/test_main.py`

Теперь мы можем написать тесты для нашего приложения. Например:

```python
import pytest

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    """Тестируем создание нового элемента."""
    response = await client.post("/items/", json={"name": "Test Item", "price": 10.0})
    
    assert response.status_code == 201  # Проверяем, что статус ответа 201 (Created)
    assert response.json() == {"id": 1, "name": "Test Item", "price": 10.0}  # Проверяем ответ

@pytest.mark.asyncio
async def test_read_item(client: AsyncClient):
    """Тестируем чтение элемента по ID."""
    await client.post("/items/", json={"name": "Test Item", "price": 10.0})  # Создаем элемент
    
    response = await client.get("/items/1")  # Запрашиваем элемент по ID
    
    assert response.status_code == 200  # Проверяем статус ответа
    assert response.json() == {"id": 1, "name": "Test Item", "price": 10.0}  # Проверяем данные элемента
```

### Управление сессией в тестах

1. **Создание сессии**: В фикстуре `db_session` мы создаем новую асинхронную сессию для каждого теста. Это позволяет каждому тесту работать с изолированной копией базы данных.

2. **Переопределение зависимостей**: В фиктуре `client` мы переопределяем зависимость получения сессии (`get_db`) на созданную сессию. Это позволяет вашему приложению использовать эту сессию при выполнении запросов.

3. **Очистка после тестов**: В фиктуре `setup_database` вы можете добавить логику для очистки базы данных после выполнения тестов (например, удаление всех записей или сброс состояния).

Эта структура позволяет эффективно управлять состоянием базы данных и обеспечивает изолированное выполнение каждого теста, что критически важно для надежности тестирования.

Citations:
[1] https://dev.to/whchi/testing-fastapi-with-async-database-session-1b5d
[2] https://github.com/fastapi/fastapi/discussions/8415
[3] https://weirdsheeplabs.com/blog/fast-and-furious-async-testing-with-fastapi-and-pytest
[4] https://github.com/fastapi/fastapi/issues/5692
[5] https://fastapi.tiangolo.com/advanced/async-tests/
[6] https://stackoverflow.com/questions/71763595/pytestfastapisqlalchemypostgres-interfaceerror
[7] https://testdriven.io/blog/fastapi-crud/
---
### Зачем нужна функция `event_loop`?

Функция `event_loop`, как правило, используется для создания и управления циклом событий в асинхронных тестах. В контексте `pytest-asyncio`, она позволяет обеспечить, что каждый тест будет выполняться с новым циклом событий, что критически важно для изоляции тестов и предотвращения конфликтов между ними.

#### Как она используется в тестах?

1. **Создание нового цикла событий**: В функции `event_loop` создается новый цикл событий с помощью `asyncio.new_event_loop()`.
2. **Установка текущего цикла**: С помощью `asyncio.set_event_loop(loop)` устанавливается созданный цикл как текущий.
3. **Очистка после теста**: После завершения теста цикл закрывается с помощью `loop.close()`, что позволяет избежать утечек ресурсов.

Это гарантирует, что каждый тест имеет свой собственный цикл событий, который не будет мешать другим тестам.

### Почему клиент создается без использования `transport=ASGITransport()`?

В примере, который я предоставил, клиент создается без явного указания `transport=ASGITransport()`, потому что:

- **Использование FastAPI**: При использовании FastAPI с `httpx` в контексте асинхронного тестирования, клиент может быть инициализирован напрямую с приложением FastAPI без необходимости указывать транспорт. Это возможно благодаря тому, что `httpx.AsyncClient` может работать с ASGI-приложениями напрямую.
  
- **Упрощение кода**: Указание транспорта может быть излишним в некоторых случаях, особенно если вы используете стандартные настройки и не планируете изменять поведение клиента. В большинстве случаев FastAPI и `httpx` могут корректно работать вместе без дополнительных настроек транспорта.

Тем не менее, если требуется более детальная настройка или использование специфических функций ASGI, можно явно указать транспорт:

```python
async with AsyncClient(app=test_app, transport=ASGITransport(), base_url="http://test") as client:
```

### Заключение

Функция `event_loop` позволяет управлять циклом событий в асинхронных тестах, обеспечивая изоляцию и предотвращая конфликты между тестами. Клиент может быть создан без явного указания транспорта в простых случаях, но для более сложных настроек можно использовать `ASGITransport`.

Citations:
[1] https://habr.com/ru/companies/otus/articles/337108/
[2] https://javarush.com/quests/lectures/ru.javarush.python.core.lecture.level14.lecture05