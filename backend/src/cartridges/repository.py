from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.cartridges import models, schemas
from src.printers.models import Printer  # Импортируем модель принтера

class CartridgesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[models.Cartridge]:
        # selectinload нужен, чтобы SQLAlchemy подтянула связанные принтеры
        result = await self.db.execute(select(models.Cartridge).options(selectinload(models.Cartridge.printers)))
        return list(result.scalars().all())

    async def get_by_id(self, cartridge_id: UUID) -> Optional[models.Cartridge]:
        result = await self.db.execute(
            select(models.Cartridge)
            .where(models.Cartridge.id == cartridge_id)
            .options(selectinload(models.Cartridge.printers))
        )
        return result.scalars().first()

    async def create(self, data: schemas.CartridgeCreate) -> models.Cartridge:
        data_dict = data.model_dump()
        printer_ids = data_dict.pop("printer_ids", [])

        if data_dict.get("shop_link"):
            data_dict["shop_link"] = str(data_dict["shop_link"])

        cartridge = models.Cartridge(**data_dict)

        # Привязываем принтеры
        if printer_ids:
            printers = await self.db.execute(select(Printer).where(Printer.id.in_(printer_ids)))
            cartridge.printers = list(printers.scalars().all())

        self.db.add(cartridge)
        await self.db.commit()
        await self.db.refresh(cartridge)
        return cartridge

    async def update(self, cartridge: models.Cartridge, data: schemas.CartridgeUpdate) -> models.Cartridge:
        data_dict = data.model_dump(exclude_unset=True)
        printer_ids = data_dict.pop("printer_ids", None)

        if "shop_link" in data_dict and data_dict["shop_link"] is not None:
            data_dict["shop_link"] = str(data_dict["shop_link"])

        for key, value in data_dict.items():
            setattr(cartridge, key, value)

        # Обновляем связи с принтерами, если они были переданы
        if printer_ids is not None:
            printers = await self.db.execute(select(Printer).where(Printer.id.in_(printer_ids)))
            cartridge.printers = list(printers.scalars().all())

        await self.db.commit()
        await self.db.refresh(cartridge)
        return cartridge

    async def delete(self, cartridge: models.Cartridge) -> None:
        await self.db.delete(cartridge)
        await self.db.commit()