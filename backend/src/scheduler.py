import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Printer
from .printer_parser import fetch_printer_data

logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO)


async def update_all_printers():
    """Опрашивает все принтеры в базе данных и обновляет их состояние"""
    db: Session = SessionLocal()
    try:
        # Ищем все принтеры с заполненным IP-адресом
        printers = (
            db.query(Printer)
            .filter(Printer.ip_address != None, Printer.ip_address != "")
            .all()
        )
        if not printers:
            return

        logger.info(
            f"Запуск периодического опроса принтеров. Найдено принтеров: {len(printers)}"
        )

        # Опрашиваем принтеры параллельно
        async def update_single_printer(printer_id: int, ip: str):
            try:
                data = await fetch_printer_data(ip)

                # Создаем новую сессию для каждого принтера во избежание конфликтов транзакций
                with SessionLocal() as local_db:
                    db_printer = (
                        local_db.query(Printer).filter(Printer.id == printer_id).first()
                    )
                    if db_printer:
                        db_printer.status = data["status"]
                        db_printer.toner_black = data["toner_black"]
                        db_printer.toner_cyan = data["toner_cyan"]
                        db_printer.toner_magenta = data["toner_magenta"]
                        db_printer.toner_yellow = data["toner_yellow"]

                        # Обновляем модель только если она пустая
                        if "model" in data and not db_printer.model:
                            db_printer.model = data["model"]

                        db_printer.updated_at = datetime.utcnow()
                        local_db.commit()
                        logger.info(
                            f"Принтер {ip} успешно обновлен: Статус={data['status']}, Тонер={data['toner_black']}%"
                        )
            except Exception as e:
                logger.error(
                    f"Ошибка обновления принтера ID {printer_id} по IP {ip}: {e}"
                )

        # Запускаем конкурентный опрос всех принтеров
        tasks = [update_single_printer(p.id, p.ip_address) for p in printers]
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Ошибка в планировщике опроса принтеров: {e}")
    finally:
        db.close()


async def run_scheduler(interval_seconds: int = 30):
    """Бесконечный цикл периодического опроса принтеров"""
    logger.info(
        f"Планировщик опроса принтеров запущен. Интервал: {interval_seconds} сек."
    )
    while True:
        try:
            await update_all_printers()
        except Exception as e:
            logger.error(f"Ошибка в цикле планировщика: {e}")
        await asyncio.sleep(interval_seconds)
