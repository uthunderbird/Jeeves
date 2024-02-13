from .dialog import Dialog
from .history import InMemoryHistoryStorage


class DialogManager:
    def __init__(self, storage: dict | None = None):
        if storage is None:
            storage = {}
        self.storage = storage

    def get_or_create(self, user_id: int) -> Dialog:
        if user_id not in self.storage:
            # TODO replace with factory
            self.storage[user_id] = Dialog(InMemoryHistoryStorage(), user_id)
        return self.storage[user_id]
