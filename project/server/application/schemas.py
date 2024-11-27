from typing import Optional, List, Dict, Union

from pydantic import BaseModel, ConfigDict


class BaseUser(BaseModel):
    name: str


class BaseTweet(BaseModel):
    content: str


class ErrorResponse(BaseModel):
    result: bool
    error_type: str
    error_message: str


class UserIn(BaseUser):
    api_key: str


class Followers(BaseUser):
    id: int


class Following(BaseUser):
    id: int


class SimpleUserOut(BaseUser):
    id: int


class UserOut(BaseUser):
    id: int
    followers: List[Followers] = []
    following: List[Following] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TweetIn(BaseTweet):
    tweet_media_ids: Optional[List[int]] = []


class Like(BaseModel):
    user_id: int
    name: str


class TweetOut(BaseTweet):
    id: int
    author: Dict[str, Union[int, str]]
    attachments: List[str] = []  # новое поле для вложений
    likes: List[Like] = []  # новое поле для лайков

    model_config = ConfigDict(arbitrary_types_allowed=True)
