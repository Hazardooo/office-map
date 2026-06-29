from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.cartridges import schemas
from src.cartridges.service import CartridgesService
from src.cartridges.dependencies import get_cartridges_service
from src.cartridges.exceptions import CartridgesError

router = APIRouter(prefix="/cartridges", tags=["cartridges"])

@router.get("/", response_model=List[schemas.CartridgeResponse])
async def get_all_cartridges(
        service: CartridgesService = Depends(get_cartridges_service)
):
    return await service.get_all()

@router.get("/by-printer/{printer_model}", response_model=List[schemas.CartridgeResponse])
async def get_cartridges_by_printer(
        printer_model: str,
        service: CartridgesService = Depends(get_cartridges_service)
):
    # Позволяет получить список картриджей (например, цветные + черный) для конкретной модели
    return await service.get_for_printer(printer_model)

@router.post("/", response_model=schemas.CartridgeResponse, status_code=status.HTTP_201_CREATED)
async def create_cartridge(
        data: schemas.CartridgeCreate,
        service: CartridgesService = Depends(get_cartridges_service)
):
    return await service.create(data)

@router.patch("/{cartridge_id}", response_model=schemas.CartridgeResponse)
async def update_cartridge(
        cartridge_id: UUID,
        data: schemas.CartridgeUpdate,
        service: CartridgesService = Depends(get_cartridges_service)
):
    try:
        return await service.update(cartridge_id, data)
    except CartridgesError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{cartridge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cartridge(
        cartridge_id: UUID,
        service: CartridgesService = Depends(get_cartridges_service)
):
    try:
        await service.delete(cartridge_id)
    except CartridgesError as e:
        raise HTTPException(status_code=404, detail=str(e))