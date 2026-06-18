from typing import Literal

from fastapi import APIRouter, HTTPException, Path

from src.printers.parsers import get_parser
from src.printers.schemas import TonerResponse, PrinterStatusResponse

router = APIRouter(prefix="/printers", tags=["printers"])

VENDOR_ENUM = Literal["kyocera", "canon", "hp"]


@router.get("/{vendor}/{ip}/toner", response_model=TonerResponse)
def get_printer_toner(
        vendor: VENDOR_ENUM = Path(..., description="Производитель: kyocera"),
        ip: str = Path(..., description="IP-адрес принтера")
):
    """
    Получает уровень тонера.

    **vendors:** `kyocera`
    """
    try:
        parser = get_parser(vendor, ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = parser.get_toner()

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return TonerResponse(ip=ip, vendor=vendor, toner=result)


@router.get("/{vendor}/{ip}/status", response_model=PrinterStatusResponse)
def get_printer_status(
        vendor: VENDOR_ENUM = Path(..., description="Производитель"),
        ip: str = Path(..., description="IP-адрес принтера")
):
    """Полный статус принтера."""
    try:
        parser = get_parser(vendor, ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = parser.get_status()

    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])

    return PrinterStatusResponse(
        ip=ip,
        vendor=vendor,
        model=result.get("model"),
        hostname=result.get("hostname"),
        toner=result.get("toner")
    )