from fastapi import APIRouter, HTTPException, Depends
from typing import List

from src.printers import schemas
from src.printers.dependencies import get_printer_service
from src.exceptions import PrinterNotFoundError, PrinterParseError
from src.printers.service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
async def create_printer(
        data: schemas.PrinterCreate,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return await service.create(data)
    except PrinterParseError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/", response_model=List[schemas.PrinterResponse])
async def get_all_printers(
        service: PrinterService = Depends(get_printer_service)
):
    return await service.get_all()


@router.put("/{printer_id}", response_model=schemas.PrinterResponse)
async def update_printer(
        printer_id: int,
        data: schemas.PrinterUpdate,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return await service.update(printer_id, data)
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{printer_id}/refresh", response_model=schemas.PrinterResponse)
async def refresh_printer(
        printer_id: int,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return await service.refresh(printer_id)
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PrinterParseError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{printer_id}")
async def delete_printer(
        printer_id: int,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        await service.delete(printer_id)
        return {"ok": True}
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))