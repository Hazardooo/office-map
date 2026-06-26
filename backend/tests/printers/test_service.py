import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock
from src.printers.service import PrinterService
from src.printers import schemas, models

@pytest.mark.asyncio
@patch("src.printers.service.get_parser") # Мокаем фабрику парсеров
async def test_printer_service_refresh(mock_get_parser):
    # 1. Создаем мок репозитория БД (чтобы не писать в реальную БД при тестах)
    mock_repo = MagicMock()
    mock_printer = models.Printer(
        id=uuid4(), ip="10.10.10.10", vendor="hp", name="Test"
    )
    # Имитируем, что принтер найден в БД
    mock_repo.get_by_id.return_async = mock_printer

    # 2. Создаем мок парсера (имитируем успешный опрос)
    mock_parser_instance = MagicMock()
    mock_parser_instance.get_status.return_value = {
        "model": "Fake HP Model",
        "hostname": "HOST-123",
        "toner": {
            "Черный": "85%",
            "Голубой": "20%"
        }
    }
    mock_get_parser.return_value = mock_parser_instance

    # 3. Собираем сервис с замоканным репозиторием
    service = PrinterService(db=MagicMock())
    service.repo = mock_repo # Подменяем реальный репо на фейковый

    # 4. Вызываем тестируемый метод
    await service.refresh(mock_printer.id)

    # 5. Проверяем, что сервис правильно вызвал метод обновления тонера в БД
    # Убеждаемся, что в repo.refresh_toner передался словарь, который мы сгенерировали
    mock_repo.refresh_toner.assert_called_once()
    args, kwargs = mock_repo.refresh_toner.call_args

    passed_printer = args[0]
    passed_parsed_data = args[1]

    assert passed_printer.id == mock_printer.id
    assert passed_parsed_data["model"] == "Fake HP Model"
    assert passed_parsed_data["toner"]["Черный"] == "85%"