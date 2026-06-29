from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.cartridges import models, schemas

class CartridgesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[models.Cartridge]:
        result = await self.db.execute(select(models.Cartridge))
        return list(result.scalars().all())

    async def get_by_id(self, cartridge_id: UUID) -> Optional[models.Cartridge]:
        return await self.db.get(models.Cartridge, cartridge_id)

    async def get_by_printer_model(self, printer_model: str) -> List[models.Cartridge]:
        result = await self.db.execute(
            select(models.Cartridge).where(models.Cartridge.printer_model == printer_model)
        )
        return list(result.scalars().all())

    async def create(self, data: schemas.CartridgeCreate) -> models.Cartridge:
        # Pydantic HttpUrl нужно конвертировать в строку перед записью в БД
        data_dict = data.model_dump()
        if data_dict.get("shop_link"):
            data_dict["shop_link"] = str(data_dict["shop_link"])

        cartridge = models.Cartridge(**data_dict)
        self.db.add(cartridge)
        await self.db.commit()
        await self.db.refresh(cartridge)
        return cartridge

    async def update(self, cartridge: models.Cartridge, data: schemas.CartridgeUpdate) -> models.Cartridge:
        data_dict = data.model_dump(exclude_unset=True)
        if "shop_link" in data_dict and data_dict["shop_link"] is not None:
            data_dict["shop_link"] = str(data_dict["shop_link"])

        for key, value in data_dict.items():
            setattr(cartridge, key, value)

        await self.db.commit()
        await self.db.refresh(cartridge)
        return cartridge

    async def delete(self, cartridge: models.Cartridge) -> None:
        await self.db.delete(cartridge)
        await self.db.commit()