from typing import TypeVar, Generic

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from application.database import AsyncSessionApp


T = TypeVar('T')


class BaseDAO(Generic[T]):
    model: T = None

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, options=None):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

        Аргументы:
            data_id: Критерии фильтрации в виде идентификатора записи.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        async with AsyncSessionApp() as session:
            query = select(cls.model).filter_by(id=data_id)
            if options:
                query = query.options(*options)  # Применяем опции к запросу
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, options=None, **filter_by):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

        Аргументы:
            **filter_by: Критерии фильтрации в виде именованных параметров.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        async with AsyncSessionApp() as session:
            query = select(cls.model).filter_by(**filter_by)
            if options:
                query = query.options(*options)  # Применяем опции к запросу
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, options=None, filters: dict = None, order_by: list = None, joins: list = None):
        """
        Асинхронно находит и возвращает все экземпляры модели, удовлетворяющие указанным критериям.

        Аргументы:
            session: Асинхронная сессия SQLAlchemy.
            filters: Словарь фильтров для запроса.
            order_by: Список полей для сортировки.
            joins: Список таблиц для соединения.

        Возвращает:
            Список экземпляров модели.
        """
        async with AsyncSessionApp() as session:
            query = select(cls.model)
            # Применяем соединения
            if joins:
                for join in joins:
                    query = query.outerjoin(join)  # Используем outerjoin для соединения

            if options:
                query = query.options(*options)  # Применяем опции к запросу
            if filters:
                # Применяем фильтры к запросу
                for key, value in filters.items():
                    column = getattr(cls.model, key)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))  # Для списков используем in_
                    else:
                        query = query.filter(column == value)  # Для одиночных значений
            if order_by:
                # Применяем сортировку к запросу
                for field in order_by:
                    query = query.order_by(getattr(cls.model, field))
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def add(cls, **values):
        """
        Асинхронно создает новый экземпляр модели с указанными значениями.

        Аргументы:
            **values: Именованные параметры для создания нового экземпляра модели.

        Возвращает:
            Созданный экземпляр модели.
        """
        async with AsyncSessionApp() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

    @classmethod
    async def update(cls, instance: T, **values):
        """
        Асинхронно обновляет указанные поля экземпляра модели.

        Аргументы:
            instance: Экземпляр модели, который нужно обновить.
            **values: Именованные параметры для обновления полей экземпляра модели.

        Возвращает:
            Обновленный экземпляр модели.
        """
        async with AsyncSessionApp() as session:
            async with session.begin():
                stmt = (
                    update(cls.model)
                    .where(cls.model.id == instance.id)  # Условие для обновления по ID
                    .values(**values)  # Устанавливаем новые значения
                )
                try:
                    await session.execute(stmt)  # Выполняем запрос на обновление
                    await session.commit()  # Сохраняем изменения в базе данных
                except SQLAlchemyError as e:
                    await session.rollback()  # Откатываем изменения в случае ошибки
                    raise e

            return instance  # Возвращаем обновленный экземпляр
