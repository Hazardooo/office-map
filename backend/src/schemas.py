from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --- OfficeMap Схемы ---
class OfficeMapBase(BaseModel):
    name: str


class OfficeMapCreate(OfficeMapBase):
    pass


class OfficeMapResponse(OfficeMapBase):
    id: int
    file_path: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Printer Схемы ---
class PrinterBase(BaseModel):
    name: str
    model: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = "online"
    toner_black: Optional[int] = 100
    toner_cyan: Optional[int] = None
    toner_magenta: Optional[int] = None
    toner_yellow: Optional[int] = None
    x_coordinate: float
    y_coordinate: float
    map_id: int


class PrinterCreate(PrinterBase):
    pass


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    toner_black: Optional[int] = None
    toner_cyan: Optional[int] = None
    toner_magenta: Optional[int] = None
    toner_yellow: Optional[int] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    map_id: Optional[int] = None


class PrinterResponse(PrinterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
