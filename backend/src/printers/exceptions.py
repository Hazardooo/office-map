class PrinterError(Exception):
    """Базовое исключение для принтеров."""
    pass


class PrinterNotFoundError(PrinterError):
    pass


class PrinterParseError(PrinterError):
    pass


class PrinterConnectionError(PrinterError):
    pass