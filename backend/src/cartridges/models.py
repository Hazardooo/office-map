import uuid
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from src.database.postgres import Base

class Cartridge(Base):
    __tablename__ = "cartridges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)  # Артикул, например "TK-3160"
    color = Column(String, nullable=False, default="Black")  # Black, Cyan, Magenta, Yellow
    quantity = Column(Integer, default=0, nullable=False)  # Текущий остаток на складе
    printer_model = Column(String, index=True, nullable=False)  # Связь с принтером
    shop_link = Column(Text, nullable=True)  # Ссылка на магазин (Text, так как ссылки бывают длинными)