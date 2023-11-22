# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class FinancialRecord(Base):
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True)
    product = Column(String)
    quantity = Column(Integer)
    status = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Для установки соединения с базой данных
engine = create_engine('sqlite:///financial_records.db', echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
