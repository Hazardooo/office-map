# src/printers/parsers/exceptions.py
from src.printers.exceptions import PrinterError

class ParserError(PrinterError):
    """Базовое исключение для ошибок модуля парсинга."""
    pass

class PoolTimeoutError(ParserError):
    """Выбрасывается, когда нет доступных драйверов в пуле."""
    pass

class ParserTimeoutError(ParserError):
    """Выбрасывается, когда принтер не отвечает (сетевой таймаут)."""
    pass

class ParserAuthError(ParserError):
    """Выбрасывается, если не удалось пройти авторизацию на веб-интерфейсе принтера."""
    pass

class ParserDOMError(ParserError):
    """Выбрасывается, если структура HTML/DOM принтера не соответствует ожидаемой."""
    pass

class ParserUnknownModelError(ParserError):
    """Выбрасывается, если парсер не может определить модель устройства."""
    pass