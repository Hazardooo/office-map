from sqlalchemy.orm import Session

from src.printers.repository import PrinterRepository
from src.printers.parsers import get_parser
from src.printers import schemas
from src.printers.exceptions import PrinterNotFoundError, PrinterParseError


class PrinterService:
    def __init__(self, db: Session):
        self.repo = PrinterRepository(db)

    def create(self, data: schemas.PrinterCreate) -> schemas.PrinterResponse:
        parser = get_parser(data.vendor, data.ip)
        parsed = parser.get_status()

        if "error" in parsed:
            raise PrinterParseError(parsed["error"])

        printer = self.repo.create(data, parsed)
        return schemas.PrinterResponse.model_validate(printer)

    def get_all(self) -> list[schemas.PrinterResponse]:
        printers = self.repo.get_all()
        return [schemas.PrinterResponse.model_validate(p) for p in printers]

    def update(self, printer_id: int, data: schemas.PrinterUpdate) -> schemas.PrinterResponse:
        printer = self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")

        updated = self.repo.update(printer, data)
        return schemas.PrinterResponse.model_validate(updated)

    def refresh(self, printer_id: int) -> schemas.PrinterResponse:
        printer = self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")

        parser = get_parser(printer.vendor, printer.ip)
        parsed = parser.get_status()

        if "error" in parsed:
            raise PrinterParseError(parsed["error"])

        refreshed = self.repo.refresh_toner(printer, parsed)
        return schemas.PrinterResponse.model_validate(refreshed)

    def delete(self, printer_id: int) -> None:
        printer = self.repo.get_by_id(printer_id)
        if not printer:
            raise PrinterNotFoundError(f"Принтер {printer_id} не найден")

        self.repo.delete(printer)