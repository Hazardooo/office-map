from pathlib import Path
from fastapi import Depends

from src.maps.repository import IMapRepository, FileSystemMapRepository
from src.maps.service import MapService, MapFileValidator, IValidator


UPLOAD_DIR = Path("uploads/maps")


def get_upload_dir() -> Path:
    return UPLOAD_DIR


def get_repository(upload_dir: Path = Depends(get_upload_dir)) -> IMapRepository:
    """Фабрика репозитория. Можно подменить на S3/MinIO без изменения роутеров."""
    return FileSystemMapRepository(upload_dir)


def get_validator() -> IValidator:
    """Фабрика валидатора. Правила валидации вынесены в конфигурацию."""
    return MapFileValidator(
        allowed_types={
            "image/svg+xml",  # Только SVG, как в оригинальном router.py
        },
        allowed_extensions={"svg"},
        max_size_mb=10.0,
    )


def get_map_service(
        repo: IMapRepository = Depends(get_repository),
        validator: IValidator = Depends(get_validator),
) -> MapService:
    """Фабрика сервиса. Все зависимости инжектятся извне (DIP)."""
    return MapService(repository=repo, validator=validator)