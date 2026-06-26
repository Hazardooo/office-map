# src/printers/service.py
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.printers.repository import PrinterRepository
from src.printers.parsers import get_parser
from src.printers import schemas, models
from src.printers.exceptions import PrinterNotFoundError, PrinterParseError


class PrinterService:
    def __init__(self, db: AsyncSession):
        self.repo = PrinterRepository(db)

    async def create(self, data: schemas.PrinterCreate) -> models.Printer:
        # Проверяем уникальность IP на уровне бизнес-логики
        existing_printer = await self.repo.get_by_ip(data.ip)
        if existing_printer:
            raise PrinterParseError(
                f"Принтер с IP-адресом {data.ip} уже зарегистрирован под именем '{existing_printer.name}'")

        parser = get_parser(data.vendor, data.ip)

        try:
            # Увеличен таймаут до 60 секунд для медленных физических принтеров
            parsed = await asyncio.wait_for(
                asyncio.to_thread(parser.get_status),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            raise PrinterParseError(f"Таймаут опроса принтера ({data.ip}). Устройство слишком долго отвечает.")
        except Exception as e:
            raise PrinterParseError(f"Ошибка сетевого подключения к принтеру: {str(e)}")

        if "error" in parsed:
            raise PrinterParseError(parsed["error"])

        return await self.repo.create(data, parsed)

    async def get_all(self) -> List[models.Printer]:
        return await self.repo.get_all()

    async def update(self, printer_id: UUID, data: schemas.PrinterUpdate) -> models.Printer:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер с ID {printer_id} не найден")
        return await self.repo.update(printer, data)

    async def refresh(self, printer_id: UUID) -> models.Printer:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер с ID {printer_id} не найден")

        parser = get_parser(printer.vendor, printer.ip)

        try:
            parsed = await asyncio.wait_for(
                asyncio.to_thread(parser.get_status),
                timeout=60.0
            )
        except (asyncio.TimeoutError, Exception):
            return await self.repo.set_offline(printer)

        if "error" in parsed:
            return await self.repo.set_offline(printer)

        return await self.repo.refresh_toner(printer, parsed)

    async def delete(self, printer_id: UUID) -> None:
        printer = await self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер с ID {printer_id} не найден")
        await self.repo.delete(printer)
