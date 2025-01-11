Чтобы подключить Alembic к вашему проекту и настроить его для работы с асинхронной базой данных, выполните следующие шаги. Эта инструкция охватывает инициализацию Alembic, настройку конфигурации, создание миграций и их применение.

## Шаг 1: Установка Alembic

Если вы еще не установили Alembic, выполните следующую команду в вашем виртуальном окружении:

```bash
pip install alembic[async]
```

## Шаг 2: Инициализация Alembic

Запустите команду для инициализации Alembic в вашем проекте:

```bash
alembic init -t async alembic
```

Эта команда создаст каталог `alembic`, в котором будут находиться файлы конфигурации и директория для миграций.

## Шаг 3: Настройка файла `alembic.ini`

Откройте файл `alembic.ini` и убедитесь, что строка подключения к вашей базе данных правильно настроена. Например:

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://admin:admin@172.18.0.2:5432/twitter
```

Замените `172.18.0.2` на IP-адрес вашего контейнера или сервера PostgreSQL.

## Шаг 4: Настройка файла `env.py`

Откройте файл `alembic/env.py` и внесите следующие изменения:

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from application.models import BaseProj

config = context.config

# Установите строку подключения к базе данных
config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://admin:admin@172.18.0.2:5432/twitter")

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseProj.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

## Шаг 5: Создание миграции

Теперь вы можете создать первую миграцию с помощью команды:

```bash
alembic revision -m "Init migration" --autogenerate
```

Эта команда создаст файл миграции в директории `alembic/versions`, который будет содержать изменения схемы на основе ваших моделей.

## Шаг 6: Применение миграции

Чтобы применить созданные миграции к базе данных, используйте команду:

```bash
alembic upgrade head
```

Эта команда применит все миграции до последней версии.

## Дополнительные команды Alembic

- **Просмотр текущей версии** базы данных:
  ```bash
  alembic current
  ```

- **Откат миграции** на одну версию назад:
  ```bash
  alembic downgrade -1
  ```

- **Создание новой миграции** без автогенерации (пустая миграция):
  ```bash
  alembic revision -m "New migration"
  ```

## Заключение

Теперь у вас есть полная инструкция по подключению Alembic к вашему проекту с использованием асинхронного SQLAlchemy. Следуя этим шагам, вы сможете эффективно управлять миграциями вашей базы данных.

Citations:
[1] https://hellowac.github.io/alembic-doc-zh/en/api/commands.html
[2] https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html
[3] https://alembic.sqlalchemy.org/en/latest/api/commands.html
[4] https://stackoverflow.com/questions/70203927/how-to-prevent-alembic-revision-autogenerate-from-making-revision-file-if-it-h/71212675
[5] https://habr.com/ru/articles/585228/
[6] https://alembic.sqlalchemy.org/en/latest/autogenerate.html
[7] https://alembic.sqlalchemy.org/en/latest/tutorial.html
[8] https://geoalchemy-2.readthedocs.io/en/latest/alembic.html