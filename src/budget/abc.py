import abc
import typing
import uuid

from records.transaction import TransactionRecord


class AbstractBudgetRepository(abc.ABC):

    @abc.abstractmethod
    def add_transaction(self, transaction_record: TransactionRecord) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def edit_transaction(self, transaction_id: uuid.UUID, **modifications: dict) -> TransactionRecord:
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_transaction(self, transaction_id: uuid.UUID) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def last_transactions(self, amount=5) -> typing.List[TransactionRecord]:
        raise NotImplementedError


BudgetRepositoryT = typing.TypeVar("BudgetRepositoryT", bound=AbstractBudgetRepository)
