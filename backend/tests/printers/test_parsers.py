import pytest
from unittest.mock import patch, MagicMock
from src.printers.parsers.hp import HPParser
from src.printers.parsers.canon import CanonParser

def load_fixture(filename: str) -> str:
    """Загружает HTML-дамп для мока."""
    with open(f"tests/printers/fixtures/{filename}", "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------------------------------------
# ТЕСТ HP (Мокаем requests.get)
# ---------------------------------------------------------
@patch("src.printers.parsers.hp.requests.get")
def test_hp_parser_with_mock(mock_get):
    # 1. Подготавливаем фейковый ответ от "принтера"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = load_fixture("hp_page_structure3.html") # Дамп от M425dn
    mock_get.return_value = mock_response

    # 2. Вызываем парсер
    parser = HPParser("127.0.0.1")
    result = parser.get_status()

    # 3. Проверяем, что парсер правильно разобрал HTML-дамп
    assert "error" not in result
    assert result["model"] == "HP LaserJet 400 MFP M425dn"
    assert result["hostname"] == "NPIE75959"
    # Согласно твоему дампу hp_page_structure4.html, там пустой картридж ("--%")
    assert result["toner"]["Черный"] == "0%"

# ---------------------------------------------------------
# ТЕСТ CANON (Мокаем Selenium Driver Pool)
# ---------------------------------------------------------
@patch("src.printers.parsers.canon.get_pool")
def test_canon_parser_with_mock(mock_get_pool):
    # 1. Мокаем веб-драйвер Selenium
    mock_driver = MagicMock()
    # Подсовываем дамп портала
    mock_driver.page_source = load_fixture("canon_page_structure.html")
    mock_driver.current_url = "http://127.0.0.1:8000/rps/portal.cgi?CSUT=123"

    # Настраиваем пул, чтобы он отдавал наш замоканный драйвер
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = mock_driver
    mock_get_pool.return_value = mock_pool

    # 2. Вызываем парсер
    parser = CanonParser("127.0.0.1")
    result = parser.get_status()

    # 3. Проверяем результат
    assert "error" not in result
    # Здесь впиши ожидаемые данные из твоего дампа Canon
    # assert result["toner"]["Черный"] == "70%"