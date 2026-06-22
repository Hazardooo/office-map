from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.printers.router import router as printers_router
from src.maps.router import router as maps_router
from src.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    description=f"{settings.APP_NAME} API",
    version="1.0.0",
    root_path="/api",
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
