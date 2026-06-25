# src/printers/parsers/base.py
from typing import Dict, Any

class BasePrinterParser:
    """Базовый класс для всех парсеров принтеров."""

    def __init__(self, ip: str):
        self.ip = ip
        # Большинство принтеров используют HTTP, если Kyocera строго HTTPS — можно переопределить в классе
        self.base_url = f"http://{ip}"

    def get_status(self) -> Dict[str, Any]:
        """Возвращает полный статус принтера."""
        raise NotImplementedError("Метод get_status должен быть реализован в подклассах")

    def _set_driver_timeouts(self, driver):
        """Устанавливает лимиты времени, чтобы Selenium не зависал на битых хостах."""
        driver.set_page_load_timeout(20)
        driver.set_script_timeout(20)