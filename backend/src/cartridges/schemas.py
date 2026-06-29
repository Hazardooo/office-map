from pydantic import BaseModel, HttpUrl, Field
from uuid import UUID
from typing import Optional

class CartridgeBase(BaseModel):
    name: str = Field(..., description="Артикул или название картриджа (например, TK-3160)")
    color: str = Field(default="Black", description="Цвет тонера")
    printer_model: str = Field(..., description="Модель совместимого принтера")
    shop_link: Optional[HttpUrl] = Field(None, description="Ссылка на закупку в магазине")

class CartridgeCreate(CartridgeBase):
    quantity: int = Field(default=0, ge=0, description="Начальное количество на складе")

class CartridgeUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    printer_model: Optional[str] = None
    shop_link: Optional[HttpUrl] = None

class CartridgeResponse(CartridgeBase):
    id: UUID
    quantity: int

    class Config:
        from_attributes = True