from sqlalchemy import Column, Date, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Price(Base):
    __tablename__ = "price"

    date = Column(Date, primary_key=True)
    ticker = Column(String(10), primary_key=True)
    price = Column(Numeric(13, 4))
