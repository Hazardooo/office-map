import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads/maps")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class MapService:
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml"}
    MAX_SIZE_MB = 10

    async def upload(self, file: UploadFile) -> dict:
        if file.content_type not in self.ALLOWED_TYPES:
            raise ValueError(f"Недопустимый формат: {file.content_type}. Разрешены: JPEG, PNG, WebP, SVG")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in {"jpg", "jpeg", "png", "webp", "svg"}:
            ext = "png"

        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = UPLOAD_DIR / filename

        content = await file.read()
        if len(content) > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Файл слишком большой. Максимум {self.MAX_SIZE_MB} МБ")

        with open(filepath, "wb") as f:
            f.write(content)

        return {"filename": filename, "url": f"/maps/file/{filename}"}

    def delete(self, filename: str) -> None:
        filepath = UPLOAD_DIR / filename
        if not filepath.resolve().is_relative_to(UPLOAD_DIR.resolve()):
            raise ValueError("Недопустимое имя файла")

        if filepath.exists():
            filepath.unlink()