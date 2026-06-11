from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class OfficeMap(Base):
    __tablename__ = "office_maps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Путь к SVG файлу
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    printers = relationship(
        "Printer", back_populates="office_map", cascade="all, delete-orphan"
    )


class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    # Статус принтера: online, offline, low_toner, no_paper
    status = Column(String, default="online")

    # Уровень тонера в процентах (0-100)
    toner_black = Column(Integer, default=100)
    toner_cyan = Column(Integer, default=None, nullable=True)  # Для цветных
    toner_magenta = Column(Integer, default=None, nullable=True)  # Для цветных
    toner_yellow = Column(Integer, default=None, nullable=True)  # Для цветных

    # Координаты на карте (в процентах от размера контейнера, 0.0 - 100.0)
    x_coordinate = Column(Float, nullable=False)
    y_coordinate = Column(Float, nullable=False)

    map_id = Column(
        Integer, ForeignKey("office_maps.id", ondelete="CASCADE"), nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    office_map = relationship("OfficeMap", back_populates="printers")
