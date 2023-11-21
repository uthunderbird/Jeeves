from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class FinancialRecord(Base):
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    user_message = Column(String)
    product = Column(String)
    price = Column(Integer)
    quantity = Column(Integer)
    status = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///financial_records.db', echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
