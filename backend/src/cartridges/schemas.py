from pydantic import BaseModel, HttpUrl, Field
from uuid import UUID
from typing import Optional, List

class CartridgeBase(BaseModel):
    name: str = Field(..., description="Артикул или название картриджа (например, TK-3160)")
    color: str = Field(default="Black", description="Цвет тонера")
    shop_link: Optional[HttpUrl] = Field(None, description="Ссылка на закупку в магазине")

class CartridgeCreate(CartridgeBase):
    quantity: int = Field(default=0, ge=0)
    printer_ids: List[UUID] = Field(default_factory=list, description="Список ID принтеров, к которым подходит картридж")

class CartridgeUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    shop_link: Optional[HttpUrl] = None
    printer_ids: Optional[List[UUID]] = None

class CartridgeResponse(CartridgeBase):
    id: UUID
    quantity: int
    printer_ids: List[UUID] = Field(default_factory=list)

    class Config:
        from_attributes = True