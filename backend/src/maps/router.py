from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from src.maps.dependencies import get_map_service, get_upload_dir
from src.maps.exceptions import MapError, InvalidFormatError, FileTooLargeError
from src.maps.schemas import MapUploadResponse, MapCurrentResponse
from src.maps.repository import FileSystemMapRepository
from src.maps.service import MapService

router = APIRouter(prefix="/maps", tags=["maps"])


@router.post("/upload", response_model=MapUploadResponse)
async def upload_map(
        file: UploadFile = File(...),
        service: MapService = Depends(get_map_service),
):
    try:
        map_file = await service.upload(file)
        return MapUploadResponse(
            url=map_file.url,
            filename=map_file.filename,
            size_bytes=map_file.size_bytes,
        )
    except InvalidFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except MapError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=MapCurrentResponse)
async def get_current_map(service: MapService = Depends(get_map_service)):
    map_file = await service.get_current()
    if not map_file:
        raise HTTPException(status_code=404, detail="Карта ещё не загружена")
    return MapCurrentResponse(
        url=map_file.url,
        filename=map_file.filename,
        uploaded_at=map_file.uploaded_at,
    )


@router.get("/file/{filename}")
async def get_map_file(
        filename: str,
        upload_dir=Depends(get_upload_dir),
):
    """Раздача статики. Роутер делегирует файловую систему, но не управляет ей напрямую."""
    repo = FileSystemMapRepository(upload_dir)
    map_file = await repo.get_by_filename(filename)
    if not map_file:
        raise HTTPException(status_code=404, detail="Файл карты не найден")
    return FileResponse(map_file.path)
