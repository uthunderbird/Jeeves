import typing

from pydantic.v1 import BaseModel


class User(BaseModel):
    user_id: int


UserT = typing.TypeVar("UserT", bound=User)
