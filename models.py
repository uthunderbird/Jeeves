from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
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

class FinancialRecord(Base):
    __tablename__ = 'financial_records'

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(Integer)
    username = Column(String)
    user_message = Column(String)
    product = Column(String)
    price = Column(Integer)
    quantity = Column(Integer)
    status = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
