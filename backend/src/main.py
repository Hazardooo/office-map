from fastapi import FastAPI
from printers.router import router as printers_router

app = FastAPI()

app.include_router(printers_router)