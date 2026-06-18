from sqlalchemy.orm import Session
from typing import List, Optional

from src.printers import models, schemas


class PrinterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, printer_id: int) -> Optional[models.Printer]:
        return self.db.query(models.Printer).filter(models.Printer.id == printer_id).first()

    def get_by_ip(self, ip: str) -> Optional[models.Printer]:
        return self.db.query(models.Printer).filter(models.Printer.ip == ip).first()

    def get_all(self) -> List[models.Printer]:
        return self.db.query(models.Printer).all()

    def create(self, data: schemas.PrinterCreate, parsed: dict) -> models.Printer:
        toner = parsed.get("toner", {})
        toner_black = int(toner.get("Черный", "100%").replace("%", ""))

        db_printer = models.Printer(
            name=data.name or parsed.get("hostname") or parsed.get("model") or f"Printer {data.ip}",
            ip=data.ip,
            vendor=data.vendor,
            model=parsed.get("model"),
            hostname=parsed.get("hostname"),
            x=data.x,
            y=data.y,
            toner_black=toner_black,
            status=parsed.get("status", "unknown"),
        )
        self.db.add(db_printer)
        self.db.commit()
        self.db.refresh(db_printer)
        return db_printer

    def update(self, printer: models.Printer, data: schemas.PrinterUpdate) -> models.Printer:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(printer, field, value)
        self.db.commit()
        self.db.refresh(printer)
        return printer

    def refresh_toner(self, printer: models.Printer, parsed: dict) -> models.Printer:
        toner = parsed.get("toner", {})
        printer.toner_black = int(toner.get("Черный", "100%").replace("%", ""))
        printer.status = parsed.get("status", "unknown")
        self.db.commit()
        self.db.refresh(printer)
        return printer

    def delete(self, printer: models.Printer) -> None:
        self.db.delete(printer)
        self.db.commit()
