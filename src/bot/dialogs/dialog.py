import typing

from pydantic.v1 import BaseModel
from telebot.types import Message

from bot.dialogs.history import HistoryStorageT
from records.user import UserT


class Action(BaseModel):
    actor: typing.Literal['user', 'ai']
    is_external: bool
    readable_representation: str


class Dialog:

    def __repr__(self):
        return repr(self._storage)

    def __init__(
        self,
        history_storage: HistoryStorageT,
        user: UserT,
    ):
        self.user = user
        self._storage = history_storage

    async def add_message(self, message: Message):
        self._storage.add(message)
        if message.from_user.is_bot:
            await self._send_to_user(message)
        else:
            await self._send_to_ai(message)

    async def _send_to_user(self, message: Message):
        pass

    async def _send_to_ai(self, message: Message):
        pass

    async def add_action(self, action: Action):
        # TODO
        pass
