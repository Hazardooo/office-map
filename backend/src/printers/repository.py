from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import re

from src.printers import models, schemas


class PrinterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_toner(self, toner_data: dict, color_key: str, default: int = 100) -> Optional[int]:
        val = toner_data.get(color_key)
        if val is None:
            return None if color_key != "Черный" else default

        digits = re.sub(r"\D", "", str(val))
        try:
            return int(digits) if digits else default
        except ValueError:
            return default

    async def get_by_id(self, printer_id: UUID) -> Optional[models.Printer]:
        return await self.db.get(models.Printer, printer_id)

    async def get_by_ip(self, ip: str) -> Optional[models.Printer]:
        query = select(models.Printer).filter(models.Printer.ip == ip)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self) -> List[models.Printer]:
        query = select(models.Printer)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: schemas.PrinterCreate, parsed: dict) -> models.Printer:
        toner = parsed.get("toner", {})

        # is_online определяется по результату парсинга
        is_online = "error" not in parsed

        db_printer = models.Printer(
            name=data.name or parsed.get("hostname") or parsed.get("model") or f"Printer {data.ip}",
            ip=data.ip,
            vendor=data.vendor,
            model=parsed.get("model"),
            x=data.x,
            y=data.y,
            toner_black=self._parse_toner(toner, "Черный", 100),
            toner_cyan=self._parse_toner(toner, "Голубой"),
            toner_magenta=self._parse_toner(toner, "Пурпурный"),
            toner_yellow=self._parse_toner(toner, "Желтый"),
            is_online=is_online,
        )
        self.db.add(db_printer)
        await self.db.commit()
        await self.db.refresh(db_printer)
        return db_printer

    async def update(self, printer: models.Printer, data: schemas.PrinterUpdate) -> models.Printer:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(printer, field, value)
        await self.db.commit()
        await self.db.refresh(printer)
        return printer

    async def refresh_toner(self, printer: models.Printer, parsed: dict) -> models.Printer:
        toner = parsed.get("toner", {})

        printer.toner_black = self._parse_toner(toner, "Черный", 100)
        printer.toner_cyan = self._parse_toner(toner, "Голубой")
        printer.toner_magenta = self._parse_toner(toner, "Пурпурный")
        printer.toner_yellow = self._parse_toner(toner, "Желтый")

        # is_online обновляем на основе результата парсинга
        printer.is_online = "error" not in parsed

        if parsed.get("serial_number"):
            printer.serial_number = parsed.get("serial_number")

        await self.db.commit()
        await self.db.refresh(printer)
        return printer

    async def set_offline(self, printer: models.Printer) -> models.Printer:
        """Устанавливает is_online=False при ошибке парсинга."""
        printer.is_online = False
        await self.db.commit()
        await self.db.refresh(printer)
        return printer

    async def delete(self, printer: models.Printer) -> None:
        await self.db.delete(printer)
        await self.db.commit()
