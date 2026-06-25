import pytest
from unittest.mock import MagicMock
from uuid import uuid4


# ─── Фикстуры для парсеров ───

@pytest.fixture
def mock_driver():
    """Мок Selenium WebDriver."""
    driver = MagicMock()
    driver.get = MagicMock()
    driver.page_source = """
    <html>
        <frame name="wlmframe">
            <frame name="toner">
                <table id="contentrow">
                    <tr><td>Черный</td><td>56%</td></tr>
                    <tr><td>Голубой</td><td>73%</td></tr>
                    <tr><td>Пурпурный</td><td>60%</td></tr>
                    <tr><td>Желтый</td><td>52%</td></tr>
                </table>
            </frame>
        </frame>
    </html>
    """
    driver.switch_to.frame = MagicMock()
    driver.switch_to.default_content = MagicMock()
    driver.delete_all_cookies = MagicMock()
    return driver


@pytest.fixture
def mock_pool(mock_driver):
    """Мок пула драйверов с одним драйвером."""
    from src.printers.parsers.pool import DriverPool
    pool = MagicMock(spec=DriverPool)
    pool.acquire = MagicMock(return_value=mock_driver)
    pool.release = MagicMock()
    return pool


# ─── Фикстуры для моделей ───

@pytest.fixture
def sample_printer():
    """Тестовый принтер (как в БД)."""
    from src.printers.models import Printer
    printer = MagicMock(spec=Printer)
    printer.id = uuid4()
    printer.name = "Руководство"
    printer.ip = "10.100.0.34"
    printer.vendor = "kyocera"
    printer.model = "ECOSYS P3060dn"
    printer.hostname = "Unknown"
    printer.serial_number = None
    printer.x = 100.0
    printer.y = 200.0
    printer.toner_black = 100
    printer.toner_cyan = 100
    printer.toner_magenta = 100
    printer.toner_yellow = 100
    printer.is_online = True
    return printer


@pytest.fixture
def printer_create_data():
    """Данные для создания принтера."""
    from src.printers.schemas import PrinterCreate
    return PrinterCreate(
        ip="10.100.0.34",
        vendor="kyocera",
        x=100.0,
        y=200.0,
        name="Руководство",
    )


@pytest.fixture
def kyocera_status_response():
    """Успешный ответ от KyoceraParser.get_status()."""
    return {
        "model": "ECOSYS P3060dn",
        "hostname": "Unknown",
        "toner": {
            "Черный": "56%",
            "Голубой": "73%",
            "Пурпурный": "60%",
            "Желтый": "52%",
        }
    }


@pytest.fixture
def kyocera_error_response():
    """Ошибка от KyoceraParser."""
    return {"error": "Нет доступных драйверов"}