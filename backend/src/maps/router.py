from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse

from src.maps.dependencies import get_map_service, get_upload_dir
from src.maps.schemas import MapUploadResponse, MapCurrentResponse
from src.maps.repository import FileSystemMapRepository
from src.maps.service import MapService

router = APIRouter(prefix="/maps", tags=["maps"])


@router.post("/upload", response_model=MapUploadResponse)
async def upload_map(
        file: UploadFile = File(...),
        service: MapService = Depends(get_map_service),
):
    map_file = await service.upload(file)
    return MapUploadResponse(
        url=map_file.url,
        filename=map_file.filename,
        size_bytes=map_file.size_bytes,
    )


@router.get("/current", response_model=MapCurrentResponse)
async def get_current_map(service: MapService = Depends(get_map_service)):
    map_file = await service.get_current()
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
    repo = FileSystemMapRepository(upload_dir)
    map_file = await repo.get_by_filename(filename)
    return FileResponse(map_file.path)