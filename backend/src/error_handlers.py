from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.exceptions import DBConnectionError
from src.maps.exceptions import InvalidFormatError, FileTooLargeError, MapNotFoundError, SecurityError, MapError
from src.printers.exceptions import PrinterNotFoundError, PrinterParseError, PrinterConnectionError, PrinterError


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

    # --- Printer errors ---

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

    @app.exception_handler(DBConnectionError)
    async def db_connection_handler(request: Request, exc: DBConnectionError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Database connection failed", "code": "DB_CONNECTION_ERROR"},
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
