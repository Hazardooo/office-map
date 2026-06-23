class MapError(Exception):
    """Базовое исключение для модуля карт."""
    pass


class InvalidFormatError(MapError):
    """Недопустимый формат файла."""
    pass


class FileTooLargeError(MapError):
    """Файл превышает допустимый размер."""
    pass


class MapNotFoundError(MapError):
    """Карта не найдена."""
    pass


class SecurityError(MapError):
    """Попытка доступа за пределами разрешённой директории."""
    pass