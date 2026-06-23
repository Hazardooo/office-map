import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol
from fastapi import UploadFile

from src.maps.models import MapFile
from src.maps.repository import IMapRepository
from src.maps.exceptions import InvalidFormatError, FileTooLargeError


class IValidator(Protocol):
    """Абстракция валидатора. Позволяет менять правила без изменения сервиса."""
    def validate(self, file: UploadFile, content: bytes) -> None:
        ...


class MapFileValidator:
    """Конкретная реализация валидации. Легко заменить или расширить (OCP)."""

    def __init__(
            self,
            allowed_types: Optional[set[str]] = None,
            allowed_extensions: Optional[set[str]] = None,
            max_size_mb: float = 10.0,
    ):
        self.allowed_types = allowed_types or {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/svg+xml",
        }
        self.allowed_extensions = allowed_extensions or {
            "jpg", "jpeg", "png", "webp", "svg"
        }
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)

    def validate(self, file: UploadFile, content: bytes) -> None:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

        if file.content_type not in self.allowed_types:
            raise InvalidFormatError(
                f"Недопустимый формат: {file.content_type}. "
                f"Разрешены: {', '.join(self.allowed_types)}"
            )

        if ext not in self.allowed_extensions:
            raise InvalidFormatError(
                f"Недопустимое расширение: {ext}. "
                f"Разрешены: {', '.join(self.allowed_extensions)}"
            )

        if len(content) > self.max_size_bytes:
            raise FileTooLargeError(
                f"Файл слишком большой. Максимум {self.max_size_bytes // (1024*1024)} МБ"
            )


class MapService:
    """Бизнес-логика. Зависит от абстракций, а не от конкретных реализаций (DIP)."""

    def __init__(
            self,
            repository: IMapRepository,
            validator: IValidator,
    ):
        self._repo = repository
        self._validator = validator

    async def upload(self, file: UploadFile) -> MapFile:
        content = await file.read()
        self._validator.validate(file, content)

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png", "webp", "svg"}:
            ext = "png"

        map_file = MapFile(
            id=uuid.uuid4().hex,
            filename=f"{uuid.uuid4().hex}.{ext}",
            original_name=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            uploaded_at=datetime.utcnow(),
            path=Path("."),
        )

        # Удаляем старые карты (бизнес-правило: храним только одну)
        await self._repo.clear_all()
        await self._repo.save(content, map_file)

        return map_file

    async def get_current(self) -> Optional[MapFile]:
        return await self._repo.get_latest()

    async def delete(self, filename: str) -> None:
        await self._repo.delete(filename)