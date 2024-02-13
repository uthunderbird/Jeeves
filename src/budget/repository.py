import typing

from sqlalchemy.orm import Session
from models.models import Transaction
from records.transaction import TransactionRecord
from abc import ABC
import uuid


class SQLAlchemyBudgetRepository(ABC):

    def __init__(self, session: Session):
        self.session = session

    def add_transaction(self, transaction_record: TransactionRecord, user_id: int, username: str, user_message: str) -> None:
        new_transaction = Transaction(
            user_id=user_id,
            username=username,
            user_message=user_message,
            product=transaction_record.product,
            price=transaction_record.price,
            quantity=transaction_record.quantity,
            status=transaction_record.status,
            amount=transaction_record.amount
        )
        self.session.add(new_transaction)
        self.session.commit()

    def edit_transaction(self, transaction_id: uuid.UUID, **modifications: dict) -> TransactionRecord:
        transaction = self.session.query(Transaction).filter_by(message_id=transaction_id).first()
        for key, value in modifications.items():
            setattr(transaction, key, value)
        self.session.commit()
        return transaction

    def cancel_transaction(self, transaction_id: uuid.UUID) -> None:
        transaction = self.session.query(Transaction).filter_by(message_id=transaction_id).first()
        if transaction:
            self.session.delete(transaction)
            self.session.commit()

    def last_transactions(self, amount=5) -> typing.List[TransactionRecord]:
        transactions = self.session.query(Transaction).order_by(Transaction.timestamp.desc()).limit(amount).all()
        return [TransactionRecord(
            product=t.product,
            quantity=t.quantity,
            price=t.price,
            status=t.status
        ) for t in transactions]
