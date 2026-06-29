from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.error_handlers import register_error_handlers
from src.printers.router import router as printers_router
from src.maps.router import router as maps_router
from src.cartridges.router import router as cartridges_router
from src.scheduler import PrinterScheduler
from src.settings import settings
import logging

_scheduler: PrinterScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    _scheduler = PrinterScheduler(
        max_concurrent=8,
        pool_size=8,
        interval_minutes=5
    )
    _scheduler.start()
    yield
    _scheduler.shutdown()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
app = FastAPI(
    title=settings.APP_NAME,
    description=f"{settings.APP_NAME} API",
    version="1.0.0",
    root_path="/api",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(printers_router)
app.include_router(maps_router)
app.include_router(cartridges_router)
register_error_handlers(app)
