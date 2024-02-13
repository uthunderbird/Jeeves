from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dotenv import load_dotenv
import os
from sqlalchemy.dialects.postgresql import UUID
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()


class Transaction(Base):
    __tablename__ = 'financial_records'

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(Integer)
    username = Column(String)
    user_message = Column(String)
    product = Column(String)
    price = Column(Integer)
    quantity = Column(Integer)
    status = Column(String)
    amount = Column(Integer)
    timestamp = Column(String, default=lambda: (
            datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    ).strftime('%d-%m-%y %H:%M'))


engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
