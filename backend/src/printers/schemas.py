from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class PrinterCreate(BaseModel):
    ip: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    vendor: str = Field(..., pattern=r"^(kyocera|canon|hp)$")
    x: float
    y: float
    name: Optional[str] = None


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    hostname: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    status: Optional[str] = None


class PrinterResponse(BaseModel):
    id: UUID
    name: str
    ip: str
    vendor: str
    model: Optional[str] = None
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    x: float
    y: float
    toner_black: int
    toner_cyan: Optional[int] = None
    toner_magenta: Optional[int] = None
    toner_yellow: Optional[int] = None
    status: str

    class Config:
        from_attributes = True

class PrinterListResponse(BaseModel):
    total: int
    printers: List[PrinterResponse]