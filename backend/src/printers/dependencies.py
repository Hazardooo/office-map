from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_postgres
from src.printers.service import PrinterService


def get_printer_service(db: AsyncSession = Depends(get_postgres)) -> PrinterService:
    return PrinterService(db)