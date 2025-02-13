from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///expenses.db"
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String, nullable=False, index=True) 
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

# Create tables if they don't exist
Base.metadata.create_all(engine, checkfirst=True)

SessionLocal = sessionmaker(bind=engine)