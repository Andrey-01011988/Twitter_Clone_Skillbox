import logging
from typing import TypeVar, Generic, Any

from sqlalchemy import select, update, delete, and_, Result
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseDAO(Generic[T]):
    model: T = None

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession, options=None):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанному идентификатору или None.

        Аргументы:
            data_id (int): Идентификатор записи для поиска.
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            options (list, optional): Дополнительные параметры для настройки запроса.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        logger.info("Создание запроса для поиска по ID")
        query = select(cls.model).filter_by(id=data_id)
        if options:
            query = query.options(*options)  # Применяем опции к запросу
        async with session:
            result = await session.execute(query)
        logger.info("Запрос выполнен")
        return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, options=None, **filter_by):
        """
        Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            options (list, optional): Дополнительные параметры для настройки запроса.
            **filter_by: Именованные параметры для фильтрации.

        Возвращает:
            Экземпляр модели или None, если ничего не найдено.
        """
        logger.info("Создание запроса для поиска по критериям")
        query = select(cls.model).filter_by(**filter_by)
        if options:
            query = query.options(*options)  # Применяем опции к запросу
        async with session:
            result: Result[tuple[Any]] = await session.execute(query)
        logger.info("Запрос выполнен")
        return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, session: AsyncSession, options=None, filters: dict = None, order_by: list = None,
                       joins: list = None):
        """
        Асинхронно находит и возвращает все экземпляры модели, удовлетворяющие указанным критериям.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            options (list, optional): Дополнительные параметры для настройки запроса.
            filters (dict, optional): Словарь фильтров для запроса.
            order_by (list, optional): Список полей для сортировки.
            joins (list, optional): Список таблиц для соединения.

        Возвращает:
            Список экземпляров модели.
        """
        logger.info("Создание запроса для поиска всех экземпляров")
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
        async with session:
            result = await session.execute(query)
        logger.info("Запрос выполнен")
        return result.scalars().all()

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        """
        Асинхронно создает новый экземпляр модели с указанными значениями.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            **values: Именованные параметры для создания нового экземпляра модели.

        Возвращает:
            Созданный экземпляр модели.

        Исключения:
            SQLAlchemyError: Если произошла ошибка при добавлении в базу данных.
        """
        logger.info("Создание нового экземпляра модели")

        new_instance = cls.model(**values)

        try:
            async with session.begin():
                session.add(new_instance)
                await session.commit()
                logger.info("Новый экземпляр успешно создан")
                return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при создании нового экземпляра: {e}")
            raise e

    @classmethod
    async def add_followers(cls, session: AsyncSession, account_id: int, follower_id: int):
        """
        Асинхронно добавляет новую запись о подписке между пользователями.

        :param session:
        :param account_id: Идентификатор пользователя, автора.
        :param follower_id: Идентификатор пользователя - подписчика.
        """

        # Проверяем существование записи
        existing_follow = await cls.find_one_or_none(
            account_id=account_id,
            follower_id=follower_id,
            session=session
        )

        if existing_follow:
            raise Exception("Подписка уже существует")

        async with session:
            new_follow = cls.model(account_id=account_id, follower_id=follower_id)
            session.add(new_follow)
            await session.commit()

    @classmethod
    async def update(cls, session: AsyncSession, instance: T, **values):
        """
        Асинхронно обновляет указанные поля экземпляра модели.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            instance (T): Экземпляр модели, который нужно обновить.
            **values: Именованные параметры для обновления полей экземпляра модели.

        Возвращает:
            Обновленный экземпляр модели.

        Исключения:
            SQLAlchemyError: Если произошла ошибка при обновлении в базе данных.
        """
        logger.info("Обновление экземпляра модели")

        stmt = (
            update(cls.model)
            .where(cls.model.id == instance.id)  # Условие для обновления по ID
            .values(**values)  # Устанавливаем новые значения
        )

        try:
            async with session:
                await session.execute(stmt)  # Выполняем запрос на обновление
                await session.commit()  # Сохраняем изменения в базе данных
                logger.info("Экземпляр успешно обновлен")
                return instance  # Возвращаем обновленный экземпляр
        except SQLAlchemyError as e:
            await session.rollback()  # Откатываем изменения в случае ошибки
            logger.error(f"Ошибка при обновлении экземпляра: {e}")
            raise e

    @classmethod
    async def delete(cls, session: AsyncSession, instance: T):
        """
        Асинхронно удаляет экземпляр модели.

        Аргументы:
            session (AsyncSession): Асинхронная сессия SQLAlchemy.
            instance (T): Экземпляр модели, который нужно удалить.

        Возвращает:
            bool: True, если экземпляр успешно удален.

        Исключения:
            SQLAlchemyError: Если произошла ошибка при удалении из базы данных.
        """
        logger.info("Удаление экземпляра модели")

        query_smt = (
            delete(cls.model)
            .where(cls.model.id == instance.id)
        )

        try:
            async with session:
                await session.execute(query_smt)  # Выполняем запрос на удаление
                await session.commit()  # Сохраняем изменения в базе данных
                logger.info("Экземпляр успешно удален")
                return True  # Возвращаем True при успешном удалении
        except SQLAlchemyError as e:
            await session.rollback()  # Откатываем изменения в случае ошибки
            logger.error(f"Ошибка при удалении экземпляра: {e}")
            raise e

    @classmethod
    async def delete_followers(cls, session: AsyncSession, account_id: int, follower_id: int):
        """
        Асинхронно удаляет запись о подписке между пользователями.

        :param session:
        :param follower_id: Идентификатор пользователя, который отписывается.
        :param account_id: Идентификатор пользователя, от которого отписываются.
        """
        async with session:
            async with session:
                await session.execute(
                    delete(cls.model).where(
                        and_(
                            cls.model.account_id == account_id,
                            cls.model.follower_id == follower_id
                        )
                    )
                )
                await session.commit()

