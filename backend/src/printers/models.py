from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100))
    ip = Column(String(15), unique=True, nullable=False)
    vendor = Column(String(20), nullable=False)

    model = Column(String(100))
    hostname = Column(String(100))
    serial_number = Column(String(100))

    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    toner_black = Column(Integer, default=100)
    toner_cyan = Column(Integer, nullable=True)
    toner_magenta = Column(Integer, nullable=True)
    toner_yellow = Column(Integer, nullable=True)
    status = Column(String(20), default="unknown")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)