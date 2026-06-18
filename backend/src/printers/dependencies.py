from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_postgres
from src.printers.service import PrinterService


def get_printer_service(db: Session = Depends(get_postgres)) -> PrinterService:
    return PrinterService(db)