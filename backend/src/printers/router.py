from uuid import UUID

from fastapi import APIRouter, Depends

from src.printers import schemas
from src.printers.dependencies import get_printer_service
from src.printers.schemas import PrinterListResponse
from src.printers.service import PrinterService

router = APIRouter(prefix="/printers", tags=["printers"])


@router.post("/", response_model=schemas.PrinterResponse)
async def create_printer(
        data: schemas.PrinterCreate,
        service: PrinterService = Depends(get_printer_service),
):
    return await service.create(data)


@router.get("/", response_model=PrinterListResponse)
async def get_all_printers(
        service: PrinterService = Depends(get_printer_service),
):
    printers = await service.get_all()
    return PrinterListResponse(
        total=len(printers),
        printers=printers,
    )

@router.put("/{printer_id}", response_model=schemas.PrinterResponse)
async def update_printer(
        printer_id: UUID,
        data: schemas.PrinterUpdate,
        service: PrinterService = Depends(get_printer_service),
):
    return await service.update(printer_id, data)


@router.post("/{printer_id}/refresh", response_model=schemas.PrinterResponse)
async def refresh_printer(
        printer_id: UUID,
        service: PrinterService = Depends(get_printer_service),
):
    return await service.refresh(printer_id)


@router.delete("/{printer_id}")
async def delete_printer(
        printer_id: UUID,
        service: PrinterService = Depends(get_printer_service),
):
    await service.delete(printer_id)
    return {"ok": True}