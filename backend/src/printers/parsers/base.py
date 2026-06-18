from typing import Dict


class BasePrinterParser:
    """Базовый класс для всех парсеров принтеров."""

    def __init__(self, ip: str):
        self.ip = ip
        self.base_url = f"https://{ip}"

    def get_toner(self) -> Dict[str, str]:
        """Возвращает {цвет: процент}."""
        raise NotImplementedError("Метод get_toner должен быть реализован")

    def get_status(self) -> Dict[str, str]:
        """Возвращает полный статус."""
        # По умолчанию — просто тонер
        toner = self.get_toner()
        if "error" in toner:
            return toner
        return {
            "model": "Unknown",
            "hostname": "Unknown",
            "toner": toner
        }

    def _make_url(self, path: str) -> str:
        return f"{self.base_url}{path}"