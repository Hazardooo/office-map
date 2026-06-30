from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.dragonfly import get_dragonfly
from src.database.postgres import get_postgres
from src.printers.cache import CachedPrinterRepository
from src.printers.repository import PrinterRepository
from src.printers.service import PrinterService


async def get_printer_service(
        db: AsyncSession = Depends(get_postgres),
        cache: Redis = Depends(get_dragonfly)
) -> PrinterService:
    raw_repo = PrinterRepository(db)
    cached_repo = CachedPrinterRepository(raw_repo, cache)
    return PrinterService(cached_repo)  # Сервис теперь получает "обернутый" репозиторий
