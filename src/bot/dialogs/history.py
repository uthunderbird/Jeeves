import abc
import typing

from telebot.types import Message


class AbstractHistoryStorage(abc.ABC):

    def __repr__(self) -> str:
        # Probably sometimes we can move some of this logic into __repr__ of our own Message type...
        plain = ""
        for message in self.last_messages():
            is_bot = message.from_user.is_bot
            header = f"{'Jeeves' if is_bot else 'User'} [{message.date}] #{message.message_id}"
            body = ""
            if message.reply_to_message:
                body = f"Replied to #{message.reply_to_message.message_id}\n"
            body += message.text
            plain += header + '\n' + body + "\n\n"
        return plain.strip()

    @abc.abstractmethod
    def add(self, message: Message) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def last_messages(self, amount: int = 5) -> typing.List[Message]:
        raise NotImplementedError


HistoryStorageT = typing.TypeVar("HistoryStorageT", bound=AbstractHistoryStorage)


class InMemoryHistoryStorage(AbstractHistoryStorage):
    def __init__(self):
        self._storage = []

    def add(self, message: Message) -> None:
        self._storage.append(message)

    def last_messages(self, amount: int = 5) -> typing.List[Message]:
        return self._storage[-amount:]
