from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from src.maps.service import MapService

router = APIRouter(prefix="/maps", tags=["maps"])
UPLOAD_DIR = Path("uploads/maps")
map_service = MapService()

@router.post("/upload")
async def upload_map(file: UploadFile = File(...)):
    if not file.filename.endswith(".svg"):
        raise HTTPException(400, "Разрешен только формат SVG")

    # Удаляем старые карты, чтобы не забивать диск
    for old in UPLOAD_DIR.glob("*.svg"):
        old.unlink()

    try:
        result = await map_service.upload(file)
        return {"url": result["url"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/current")
async def get_current_map():
    files = list(UPLOAD_DIR.glob("*.svg"))
    if not files:
        raise HTTPException(status_code=404, detail="Карта еще не загружена")

    # Берем самый свежий файл по времени изменения
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return {"url": f"/maps/file/{latest.name}"}

@router.get("/file/{filename}")
async def get_map_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл карты не найден")
    return FileResponse(file_path)