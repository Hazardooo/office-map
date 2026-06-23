from pydantic import BaseModel
from datetime import datetime


class MapUploadResponse(BaseModel):
    url: str
    filename: str
    size_bytes: int


class MapCurrentResponse(BaseModel):
    url: str
    filename: str
    uploaded_at: datetime


class MapFileInfo(BaseModel):
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    url: str