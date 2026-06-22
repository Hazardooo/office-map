import asyncio  # ← добавить
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.printers.repository import PrinterRepository
from src.printers.parsers import get_parser
from src.printers import schemas, models
from src.exceptions import PrinterNotFoundError, PrinterParseError


class PrinterService:
    def __init__(self, db: AsyncSession):
        self.repo = PrinterRepository(db)

    async def create(self, data: schemas.PrinterCreate) -> models.Printer:
        parser = get_parser(data.vendor, data.ip)
        parsed = await asyncio.to_thread(parser.get_status)  # ←

        if "error" in parsed:
            raise PrinterParseError(parsed["error"])

        return await self.repo.create(data, parsed)

    async def get_all(self) -> List[models.Printer]:
        return await self.repo.get_all()

    async def update(self, printer_id: int, data: schemas.PrinterUpdate) -> models.Printer:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")
        return await self.repo.update(printer, data)

    async def refresh(self, printer_id: int) -> models.Printer:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")

        parser = get_parser(printer.vendor, printer.ip)
        parsed = await asyncio.to_thread(parser.get_status)  # ←

        if "error" in parsed:
            raise PrinterParseError(parsed["error"])

        return await self.repo.refresh_toner(printer, parsed)

    async def delete(self, printer_id: int) -> None:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")
        await self.repo.delete(printer)