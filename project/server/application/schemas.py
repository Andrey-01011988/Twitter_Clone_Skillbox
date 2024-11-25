from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class BaseUser(BaseModel):
    name: str


class BaseTweet(BaseModel):
    text: str


class UserIn(BaseUser):
    api_key: str


class UserOut(BaseUser):
    id: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TweetIn(BaseTweet):
    tweet_media_ids: Optional[List[int]] = []


class TweetOut(BaseTweet):
    id: int
    timestamp: str

    model_config = ConfigDict(arbitrary_types_allowed=True)
