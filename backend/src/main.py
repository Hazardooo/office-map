import asyncio
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import OfficeMap, Printer
from .scheduler import run_scheduler
from .schemas import OfficeMapResponse, PrinterCreate, PrinterResponse, PrinterUpdate

# Автоматически создаем таблицы в БД на старте (для надежности при первом запуске)
Base.metadata.create_all(bind=engine)

# Создаем директорию для сохранения SVG карт
UPLOAD_DIR = "uploads"
MAPS_DIR = os.path.join(UPLOAD_DIR, "maps")
os.makedirs(MAPS_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем фоновую задачу опроса принтеров (интервал 30 секунд)
    scheduler_task = asyncio.create_task(run_scheduler(interval_seconds=30))
    yield
    # Отменяем задачу при завершении работы сервера
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Office Map API", version="0.1.0", lifespan=lifespan)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем папку uploads для раздачи статических SVG файлов
# Запросы вида /api/uploads/maps/... будут отдаваться статической директорией uploads/
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# --- ЭНДПОИНТЫ КАРТ ОФИСА ---


@app.post(
    "/maps/upload",
    response_model=OfficeMapResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_map(
    name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # Проверяем, что файл имеет расширение .svg
    if not file.filename.endswith(".svg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допускаются только SVG изображения.",
        )

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(MAPS_DIR, unique_filename)

    # Сохраняем файл на диск
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении файла: {str(e)}",
        )

    # Путь для сохранения в БД (будет доступен по ссылке /uploads/maps/...)
    db_file_path = f"uploads/maps/{unique_filename}"

    # Если это первая карта, автоматически делаем ее активной
    has_any_maps = db.query(OfficeMap).first() is not None
    is_active = not has_any_maps

    new_map = OfficeMap(name=name, file_path=db_file_path, is_active=is_active)

    db.add(new_map)
    db.commit()
    db.refresh(new_map)
    return new_map


@app.get("/maps", response_model=List[OfficeMapResponse])
def get_maps(db: Session = Depends(get_db)):
    return db.query(OfficeMap).order_by(OfficeMap.created_at.desc()).all()


@app.get("/maps/active", response_model=OfficeMapResponse)
def get_active_map(db: Session = Depends(get_db)):
    active_map = db.query(OfficeMap).filter(OfficeMap.is_active == True).first()
    if not active_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная карта не найдена. Пожалуйста, загрузите карту.",
        )
    return active_map


@app.post("/maps/{map_id}/activate", response_model=OfficeMapResponse)
def activate_map(map_id: int, db: Session = Depends(get_db)):
    map_to_activate = db.query(OfficeMap).filter(OfficeMap.id == map_id).first()
    if not map_to_activate:
        raise HTTPException(status_code=404, detail="Карта не найдена")

    # Делаем все остальные карты неактивными
    db.query(OfficeMap).filter(OfficeMap.id != map_id).update(
        {OfficeMap.is_active: False}
    )

    # Делаем выбранную карту активной
    map_to_activate.is_active = True
    db.commit()
    db.refresh(map_to_activate)
    return map_to_activate


@app.delete("/maps/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_map(map_id: int, db: Session = Depends(get_db)):
    db_map = db.query(OfficeMap).filter(OfficeMap.id == map_id).first()
    if not db_map:
        raise HTTPException(status_code=404, detail="Карта не найдена")

    # Удаляем физический файл с диска
    # db_map.file_path имеет вид: uploads/maps/filename.svg
    full_file_path = os.path.join(os.getcwd(), db_map.file_path)
    if os.path.exists(full_file_path):
        try:
            os.remove(full_file_path)
        except Exception as e:
            print(f"Не удалось удалить файл {full_file_path}: {e}")

    # Удаляем запись из БД (связанные принтеры удалятся каскадно)
    db.delete(db_map)
    db.commit()

    # Если удалили активную карту, делаем активной любую оставшуюся
    remaining_map = db.query(OfficeMap).first()
    if remaining_map:
        remaining_map.is_active = True
        db.commit()

    return None


# --- ЭНДПОИНТЫ ПРИНТЕРОВ ---


@app.post(
    "/printers", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED
)
def create_printer(printer_data: PrinterCreate, db: Session = Depends(get_db)):
    # Проверяем существование карты
    db_map = db.query(OfficeMap).filter(OfficeMap.id == printer_data.map_id).first()
    if not db_map:
        raise HTTPException(status_code=400, detail="Указанная карта не существует")

    new_printer = Printer(**printer_data.model_dump())
    db.add(new_printer)
    db.commit()
    db.refresh(new_printer)
    return new_printer


@app.get("/printers", response_model=List[PrinterResponse])
def get_printers(map_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Printer)
    if map_id is not None:
        query = query.filter(Printer.map_id == map_id)
    return query.all()


@app.get("/printers/{printer_id}", response_model=PrinterResponse)
def get_printer(printer_id: int, db: Session = Depends(get_db)):
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Принтер не найден")
    return printer


@app.put("/printers/{printer_id}", response_model=PrinterResponse)
def update_printer(
    printer_id: int, printer_data: PrinterUpdate, db: Session = Depends(get_db)
):
    db_printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not db_printer:
        raise HTTPException(status_code=404, detail="Принтер не найден")

    update_dict = printer_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_printer, key, value)

    db.commit()
    db.refresh(db_printer)
    return db_printer


@app.delete("/printers/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    db_printer = db.query(Printer).filter(Printer.id == printer_id).first()
    if not db_printer:
        raise HTTPException(status_code=404, detail="Принтер не найден")

    db.delete(db_printer)
    db.commit()
    return None


# Хелсчек
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return {"status": "ok"}
