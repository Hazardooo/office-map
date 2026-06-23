from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.maps.exceptions import SecurityError
from src.maps.models import MapFile


class IMapRepository(ABC):
    """Абстракция хранилища карт. Позволяет подменить реализацию
    (файловая система, S3, БД) без изменения бизнес-логики."""

    @abstractmethod
    async def save(self, file_data: bytes, map_file: MapFile) -> None:
        ...

    @abstractmethod
    async def get_latest(self) -> Optional[MapFile]:
        ...

    @abstractmethod
    async def get_by_filename(self, filename: str) -> Optional[MapFile]:
        ...

    @abstractmethod
    async def list_all(self) -> List[MapFile]:
        ...

    @abstractmethod
    async def delete(self, filename: str) -> None:
        ...

    @abstractmethod
    async def clear_all(self) -> None:
        ...


class FileSystemMapRepository(IMapRepository):
    """Реализация хранилища на файловой системе."""

    def __init__(self, upload_dir: Path):
        self._upload_dir = upload_dir
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, filename: str) -> Path:
        """Защита от Path Traversal (../../../etc/passwd)."""
        filepath = (self._upload_dir / filename).resolve()
        if not filepath.is_relative_to(self._upload_dir.resolve()):
            raise SecurityError(f"Недопустимое имя файла: {filename}")
        return filepath

    async def save(self, file_data: bytes, map_file: MapFile) -> None:
        filepath = self._upload_dir / map_file.filename
        with open(filepath, "wb") as f:
            f.write(file_data)

    async def get_latest(self) -> Optional[MapFile]:
        files = list(self._upload_dir.glob("*.*"))
        if not files:
            return None
        latest_path = max(files, key=lambda f: f.stat().st_mtime)
        return self._path_to_model(latest_path)

    async def get_by_filename(self, filename: str) -> Optional[MapFile]:
        filepath = self._validate_path(filename)
        if not filepath.exists():
            return None
        return self._path_to_model(filepath)

    async def list_all(self) -> List[MapFile]:
        return [self._path_to_model(p) for p in self._upload_dir.glob("*.*")]

    async def delete(self, filename: str) -> None:
        filepath = self._validate_path(filename)
        if filepath.exists():
            filepath.unlink()

    async def clear_all(self) -> None:
        for f in self._upload_dir.glob("*.*"):
            f.unlink()

    def _path_to_model(self, path: Path) -> MapFile:
        stat = path.stat()
        return MapFile(
            id=path.stem,
            filename=path.name,
            original_name=path.name,
            content_type=self._guess_content_type(path.suffix),
            size_bytes=stat.st_size,
            uploaded_at=datetime.fromtimestamp(stat.st_mtime),
            path=path,
        )

    @staticmethod
    def _guess_content_type(ext: str) -> str:
        mapping = {
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        return mapping.get(ext.lower(), "application/octet-stream")