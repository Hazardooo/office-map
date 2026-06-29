from uuid import UUID
from typing import List
from src.cartridges import models, schemas
from src.cartridges.repository import CartridgesRepository
from src.cartridges.exceptions import CartridgesError

class CartridgesService:
    def __init__(self, repo: CartridgesRepository):
        self.repo = repo

    async def get_all(self) -> List[models.Cartridge]:
        return await self.repo.get_all()

    async def create(self, data: schemas.CartridgeCreate) -> models.Cartridge:
        return await self.repo.create(data)

    async def update(self, cartridge_id: UUID, data: schemas.CartridgeUpdate) -> models.Cartridge:
        cartridge = await self.repo.get_by_id(cartridge_id)
        if not cartridge:
            raise CartridgesError(f"Картридж не найден")
        return await self.repo.update(cartridge, data)

    async def delete(self, cartridge_id: UUID) -> None:
        cartridge = await self.repo.get_by_id(cartridge_id)
        if not cartridge:
            raise CartridgesError(f"Картридж не найден")
        await self.repo.delete(cartridge)