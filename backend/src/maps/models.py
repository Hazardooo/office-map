from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class MapFile:
    """Доменная модель файла карты."""
    id: str
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    path: Path

    @property
    def url(self) -> str:
        return f"/maps/file/{self.filename}"