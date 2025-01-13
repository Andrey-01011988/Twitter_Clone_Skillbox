from typing import Optional, List, Dict, Union

from pydantic import BaseModel, ConfigDict, Field


class BaseUser(BaseModel):
    name: str


class BaseTweet(BaseModel):
    tweet_data: str


class ErrorResponse(BaseModel):
    result: bool
    error_type: str
    error_message: str


class UserIn(BaseUser):
    api_key: str


class Authors(BaseUser):
    id: int


class Followers(BaseUser):
    id: int


class SimpleUserOut(BaseUser):
    id: int


class UserOut(BaseUser):
    id: int
    followers: List[Authors] = Field(default_factory=list)
    following: List[Followers] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TweetIn(BaseTweet):
    tweet_media_ids: Optional[List[int]] = Field(default_factory=list)


class Like(BaseModel):
    user_id: int
    name: str


class TweetOut(BaseModel):
    id: int
    author: Dict[str, Union[int, str]]
    content: str
    attachments: List[str] = Field(default_factory=list)  # новое поле для вложений
    likes: List[Like] = Field(default_factory=list)  # новое поле для лайков

    model_config = ConfigDict(arbitrary_types_allowed=True)
