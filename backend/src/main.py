from fastapi import FastAPI
from src.printers.router import router as printers_router
from src.maps.router import router as maps_router
app = FastAPI(title="Office Map Printer Monitor")
app.include_router(printers_router, prefix="/api")
app.include_router(maps_router, prefix="/api")