# src/error_handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.database.exceptions import PostgreSQLUnavailable, DragonflyUnavailable
from src.maps.exceptions import InvalidFormatError, FileTooLargeError, MapNotFoundError, SecurityError, MapError
from src.printers.exceptions import PrinterNotFoundError, PrinterParseError, PrinterConnectionError, PrinterError

# Импортируем новые исключения парсеров
from src.printers.parsers.exceptions import (
    ParserError,
    PoolTimeoutError,
    ParserTimeoutError,
    ParserAuthError,
    ParserDOMError,
    ParserUnknownModelError
)

def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует все обработчики ошибок в приложении FastAPI."""

    # --- Map errors ---
    @app.exception_handler(InvalidFormatError)
    async def invalid_format_handler(request: Request, exc: InvalidFormatError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": "INVALID_FORMAT"},
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError):
        return JSONResponse(
            status_code=413,
            content={"detail": str(exc), "code": "FILE_TOO_LARGE"},
        )

    @app.exception_handler(MapNotFoundError)
    async def map_not_found_handler(request: Request, exc: MapNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "code": "MAP_NOT_FOUND"},
        )

    @app.exception_handler(SecurityError)
    async def security_error_handler(request: Request, exc: SecurityError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": "SECURITY_VIOLATION"},
        )

    @app.exception_handler(MapError)
    async def map_generic_handler(request: Request, exc: MapError):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "code": "MAP_ERROR"},
        )

    # --- Parser errors ---
    @app.exception_handler(PoolTimeoutError)
    async def pool_timeout_handler(request: Request, exc: PoolTimeoutError):
        return JSONResponse(
            status_code=503, # 503 Service Unavailable (сервер перегружен запросами)
            content={"detail": str(exc), "code": "POOL_TIMEOUT"},
        )

    @app.exception_handler(ParserTimeoutError)
    async def parser_timeout_handler(request: Request, exc: ParserTimeoutError):
        return JSONResponse(
            status_code=504, # 504 Gateway Timeout (принтер не ответил)
            content={"detail": str(exc), "code": "PARSER_TIMEOUT"},
        )

    @app.exception_handler(ParserAuthError)
    async def parser_auth_handler(request: Request, exc: ParserAuthError):
        return JSONResponse(
            status_code=401, # 401 Unauthorized
            content={"detail": str(exc), "code": "PARSER_AUTH_ERROR"},
        )

    @app.exception_handler(ParserDOMError)
    async def parser_dom_handler(request: Request, exc: ParserDOMError):
        return JSONResponse(
            status_code=502, # 502 Bad Gateway (принтер вернул невалидные данные)
            content={"detail": str(exc), "code": "PARSER_DOM_ERROR"},
        )

    @app.exception_handler(ParserUnknownModelError)
    async def parser_unknown_model_handler(request: Request, exc: ParserUnknownModelError):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "code": "PARSER_UNKNOWN_MODEL"},
        )

    @app.exception_handler(ParserError)
    async def parser_generic_handler(request: Request, exc: ParserError):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "code": "PARSER_ERROR"},
        )

    # --- Printer errors (Базовые) ---
    @app.exception_handler(PrinterNotFoundError)
    async def printer_not_found_handler(request: Request, exc: PrinterNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "code": "PRINTER_NOT_FOUND"},
        )

    @app.exception_handler(PrinterParseError)
    async def printer_parse_handler(request: Request, exc: PrinterParseError):
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "code": "PRINTER_PARSE_ERROR"},
        )

    @app.exception_handler(PrinterConnectionError)
    async def printer_connection_handler(request: Request, exc: PrinterConnectionError):
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "code": "PRINTER_CONNECTION_ERROR"},
        )

    @app.exception_handler(PrinterError)
    async def printer_generic_handler(request: Request, exc: PrinterError):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "code": "PRINTER_ERROR"},
        )

    # --- Database errors ---
    @app.exception_handler(PostgreSQLUnavailable)
    async def postgres_connection_handler(request: Request, exc: PostgreSQLUnavailable):
        return JSONResponse(
            status_code=503,
            content={"detail": "PostgreSQL Database connection failed", "code": "DB_CONNECTION_ERROR"},
        )

    @app.exception_handler(DragonflyUnavailable)
    async def dragonfly_connection_handler(request: Request, exc: DragonflyUnavailable):
        # Исправил опечатку в параметрах: было exc: PostgreSQLUnavailable
        return JSONResponse(
            status_code=503,
            content={"detail": "Dragonfly Database connection failed", "code": "DB_CONNECTION_ERROR"},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"detail": "Resource conflict", "code": "INTEGRITY_ERROR"},
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error", "code": "DB_ERROR"},
        )

    # --- Framework errors ---
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "code": "VALIDATION_ERROR",
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": f"HTTP_{exc.status_code}"},
        )

    # --- Fallback ---
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
        )