from fastapi import FastAPI
from src.printers.router import router as printers_router

app = FastAPI(title="Office Map Printer Monitor")

app.include_router(printers_router)