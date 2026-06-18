from pydantic import BaseModel
from typing import Dict, Optional


class TonerResponse(BaseModel):
    ip: str
    toner: Optional[Dict[str, str]] = None
    error: Optional[str] = None


class PrinterStatusResponse(BaseModel):
    ip: str
    model: Optional[str] = None
    hostname: Optional[str] = None
    toner: Optional[Dict[str, str]] = None
    error: Optional[str] = None

