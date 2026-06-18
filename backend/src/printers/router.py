from fastapi import APIRouter, HTTPException, Depends

from src.printers import schemas
from src.printers.dependencies import get_printer_service
from src.printers.exceptions import PrinterNotFoundError, PrinterParseError
from src.printers.service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
def create_printer(
        data: schemas.PrinterCreate,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return service.create(data)
    except PrinterParseError as e:
        raise HTTPException(status_code=503, detail=str(e))



@router.put("/{printer_id}", response_model=schemas.PrinterResponse)
def update_printer(
        printer_id: int,
        data: schemas.PrinterUpdate,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return service.update(printer_id, data)
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{printer_id}/refresh", response_model=schemas.PrinterResponse)
def refresh_printer(
        printer_id: int,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        return service.refresh(printer_id)
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PrinterParseError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{printer_id}")
def delete_printer(
        printer_id: int,
        service: PrinterService = Depends(get_printer_service)
):
    try:
        service.delete(printer_id)
        return {"ok": True}
    except PrinterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))