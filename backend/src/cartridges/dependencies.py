from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_postgres
from src.cartridges.repository import CartridgesRepository
from src.cartridges.service import CartridgesService

async def get_cartridges_service(db: AsyncSession = Depends(get_postgres)) -> CartridgesService:
    repo = CartridgesRepository(db)
    return CartridgesService(repo)