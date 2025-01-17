from typing import Optional, List, Dict, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseUser(BaseModel):
    name: str = Field(..., description="Имя пользователя")


class BaseTweet(BaseModel):
    tweet_data: str = Field(..., description="Содержимое твита")


class ErrorResponse(BaseModel):
    result: bool = Field(..., description="Результат выполнения запроса (успех или ошибка)")
    error_type: str = Field(..., description="Тип ошибки")
    error_message: str = Field(..., description="Сообщение об ошибке")


class UserIn(BaseUser):
    api_key: str = Field(..., description="API ключ пользователя")


class Authors(BaseUser):
    id: int = Field(..., description="Идентификатор автора")


class Followers(BaseUser):
    id: int = Field(..., description="Идентификатор подписчика")


class SimpleUserOut(BaseUser):
    id: int = Field(..., description="Идентификатор пользователя")


class UserOut(BaseUser):
    id: int = Field(..., description="Идентификатор пользователя")
    followers: List[Authors] = Field(default_factory=list, description="Список авторов подписчиков")
    following: List[Followers] = Field(default_factory=list, description="Список подписок")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TweetIn(BaseTweet):
    tweet_media_ids: Optional[List[int]] = Field(default_factory=list, description="Список идентификаторов медиа для твита")


class Like(BaseModel):
    user_id: int = Field(..., description="Идентификатор пользователя, который поставил лайк")
    name: str = Field(..., description="Имя пользователя, который поставил лайк")


class TweetOut(BaseModel):
    id: int = Field(..., description="Идентификатор твита")
    author: Dict[str, Union[int, str]] = Field(..., description="Информация об авторе твита (идентификатор и имя)")
    content: str = Field(..., description="Содержимое твита")
    attachments: List[str] = Field(default_factory=list, description="Список вложений к твиту")
    likes: List[Like] = Field(default_factory=list, description="Список лайков к твиту")

    model_config = ConfigDict(arbitrary_types_allowed=True)
