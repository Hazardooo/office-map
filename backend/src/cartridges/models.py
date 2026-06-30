import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.postgres import Base

# Промежуточная таблица для связи картриджей и принтеров (Many-to-Many)
printer_cartridge_association = Table(
    "printer_cartridge",
    Base.metadata,
    Column("printer_id", UUID(as_uuid=True), ForeignKey("printers.id", ondelete="CASCADE"), primary_key=True),
    Column("cartridge_id", UUID(as_uuid=True), ForeignKey("cartridges.id", ondelete="CASCADE"), primary_key=True)
)

class Cartridge(Base):
    __tablename__ = "cartridges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    color = Column(String, nullable=False, default="Black")
    quantity = Column(Integer, default=0, nullable=False)
    shop_link = Column(Text, nullable=True)

    # Связь с моделями принтеров
    printers = relationship("Printer", secondary=printer_cartridge_association, lazy="selectin")

    @property
    def printer_ids(self):
        return [p.id for p in self.printers]