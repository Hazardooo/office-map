from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uuid
from pathlib import Path

router = APIRouter(prefix="/maps", tags=["maps"])
UPLOAD_DIR = Path("uploads/maps")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_map(file: UploadFile = File(...)):
    if not file.filename.endswith(".svg"):
        raise HTTPException(400, "Only SVG")

    # Удаляем старую карту
    for old in UPLOAD_DIR.glob("*.svg"):
        old.unlink()

    filename = f"{uuid.uuid4().hex}.svg"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return {"url": f"/api/maps/{filename}"}


@router.get("/current")
async def get_current_map():
    files = list(UPLOAD_DIR.glob("*.svg"))
    if not files:
        raise HTTPException(404)
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return {"url": f"/api/maps/{latest.name}"}


@router.get("/{filename}")
async def serve_map(filename: str):
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(404)
    return FileResponse(filepath, media_type="image/svg+xml")