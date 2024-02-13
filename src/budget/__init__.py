import typing
import uuid

from budget.abc import BudgetRepositoryT
from records.transaction import TransactionRecord
from records.user import UserT


class BudgetService:

    def __init__(
        self,
        repo: BudgetRepositoryT,
        user: UserT
    ):
        self._repo = repo
        self._user = user

    def add_transaction(self, transaction_record: TransactionRecord):
        return self._repo.add_transaction(transaction_record)

    def edit_transaction(self, transaction_id: uuid.UUID, **modifications: dict) -> TransactionRecord:
        return self._repo.edit_transaction(transaction_id, **modifications)

    def cancel_transaction(self, transaction_id: uuid.UUID) -> None:
        return self._repo.cancel_transaction(transaction_id)

    def last_transactions(self, amount=5) -> typing.List[TransactionRecord]:
        return self._repo.last_transactions(amount)
