from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy import Integer, ForeignKey, String, DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseProj(AsyncAttrs, DeclarativeBase):
    pass


class Followers(BaseProj):
    """
    Эта модель представляет собой ассоциативную таблицу, которая связывает пользователей с их подписками.
    follower_id и followed_id являются внешними ключами, указывающими на идентификаторы пользователей в таблице users.
    Оба поля определены как первичные ключи, что позволяет избежать дублирования записей о подписках.
    """

    __tablename__ = "followers"

    follower_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    followed_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )


class Users(BaseProj):
    """
    Модель Users хранит информацию о каждом пользователе.
    Поля:
    id: уникальный идентификатор пользователя.
    name: имя пользователя.
    api_key: уникальный ключ для аутентификации пользователя.
    Связь tweets указывает на все твиты, созданные пользователем.
    Связь followers реализует отношения "многие ко многим" между пользователями:
        secondary=Followers.__tablename__: указывает на ассоциативную таблицу followers.
        primaryjoin и secondaryjoin: определяют условия соединения таблиц для получения подписчиков и подписанных пользователей.
    def __repr__(self): Возвращает строковое представление пользователя.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True)

    tweets: Mapped[List["Tweets"]] = relationship(back_populates="author")

    followers = relationship(
        "Users",
        secondary=Followers.__tablename__,
        primaryjoin=id == Followers.follower_id,
        secondaryjoin=id == Followers.followed_id,
        backref="following",
    )

    def __repr__(self):
        return f"Пользователь: {self.name}, id: {self.id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweets(BaseProj):
    """
    Модель Tweets хранит информацию о каждом твите.
    Поля:
    id: уникальный идентификатор твита.
    text: текст твита.
    timestamp: время создания твита (по умолчанию текущее время).
    author_id: идентификатор автора твита (внешний ключ).
    Связи:
    author: связь с моделью пользователей.
    likes: связь с моделью лайков.
    media: связь с моделью медиафайлов.
    def __repr__(self): Возвращает строковое представление твита.
    """

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String)
    # timestamp: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    author: Mapped["Users"] = relationship("Users", back_populates="tweets")
    likes: Mapped["Like"] = relationship(
        "Like", back_populates="tweet", cascade="all, delete-orphan"
    )
    media: Mapped["Media"] = relationship(
        "Media", back_populates="tweet", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Твит: {self.text}, создан: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, Пользователем: {self.author.name}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(BaseProj):
    """
    Модель Like связывает пользователей с твитами, которые они лайкают.
    Поля:
    id: уникальный идентификатор лайка.
    tweet_id: идентификатор твита (внешний ключ).
    user_id: идентификатор пользователя (внешний ключ).
    """

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tweet_id: Mapped[int] = mapped_column(Integer, ForeignKey("tweets.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    tweet: Mapped["Tweets"] = relationship("Tweets", back_populates="likes")
    user: Mapped["Users"] = relationship("Users")


class Media(BaseProj):
    """
    Модель Media хранит информацию о медиафайлах (например, изображениях), прикрепленных к твитам.
    Поля:
    id: уникальный идентификатор медиафайла.
    url: URL или путь к загруженному медиафайлу.
    tweet_id: идентификатор твита (внешний ключ).
    """

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String)
    tweet_id: Mapped[int] = mapped_column(Integer, ForeignKey("tweets.id"))

    tweet: Mapped["Tweets"] = relationship("Tweets", back_populates="media")
