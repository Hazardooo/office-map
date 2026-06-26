import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from src.database import Base


class Printer(Base):
    __tablename__ = "printers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    ip = Column(String(15), unique=True, nullable=False)
    vendor = Column(String(20), nullable=False)

    model = Column(String(100))

    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    toner_black = Column(Integer, default=100)
    toner_cyan = Column(Integer, nullable=True)
    toner_magenta = Column(Integer, nullable=True)
    toner_yellow = Column(Integer, nullable=True)
    is_online = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
