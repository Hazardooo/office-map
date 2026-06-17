from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.settings import  settings
from printers.printer_parser import parse

# app = FastAPI(
#     title=settings.APP_NAME,
#     description=f"{settings.APP_NAME} API",
#     version="1.0.0",
#     root_path="/api",
# )
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # app.include_router(router=urls_router, tags=["Manager"])

parse()
