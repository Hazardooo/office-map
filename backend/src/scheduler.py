import asyncio
import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.database import AsyncSessionLocal
from src.printers import models
from src.printers.parsers.pool import init_pool
from src.printers.service import PrinterService

logger = logging.getLogger(__name__)


class PrinterScheduler:
    def __init__(self, interval_minutes: int = 5, max_concurrent: int = 5, pool_size: int = 4):
        self.scheduler = AsyncIOScheduler()
        self.interval_minutes = interval_minutes
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.pool_size = pool_size

    async def _refresh_all(self):
        """Опрос всех принтеров и обновление БД."""
        async with AsyncSessionLocal() as session:
            service = PrinterService(session)
            printers: List[models.Printer] = await service.get_all()

            # Извлекаем данные в простые типы ПРИ ЖИВОЙ сессии,
            # чтобы избежать DetachedInstanceError в параллельных задачах
            printers_data = [(p.id, p.ip) for p in printers]

        if not printers_data:
            logger.info("Нет принтеров для опроса")
            return

        logger.info(f"Начинаю фоновый опрос {len(printers_data)} принтеров...")

        # Передаем id и ip раздельно в качестве атомарных значений
        tasks = [self._refresh_single(p_id, p_ip) for p_id, p_ip in printers_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False or isinstance(r, Exception))

        logger.info(f"Фоновый опрос завершён: {success} успешно, {failed} ошибок")

    async def _refresh_single(self, printer_id, printer_ip: str) -> bool:
        """Каждый принтер — изолированная сессия + ограничение concurrency."""
        async with self.semaphore:
            async with AsyncSessionLocal() as session:
                service = PrinterService(session)
                try:
                    # Сервис выполняет парсинг по ID
                    updated_printer = await service.refresh(printer_id)

                    # Проверяем статус через возвращенный из свежей сессии объект
                    if updated_printer and not updated_printer.is_online:
                        logger.warning(f"❌ Принтер {printer_ip} не обновился (переведен в offline из-за ошибки)")
                        return False

                    logger.info(f"✅ Принтер {printer_ip} успешно обновлен планировщиком.")
                    return True
                except Exception as e:
                    logger.error(f"❌ Критическая ошибка при опросе {printer_ip}: {e}")
                    return False

    def start(self):
        init_pool(max_drivers=self.pool_size)
        logger.info(f"Пул Selenium инициализирован: {self.pool_size} драйверов")

        self.scheduler.add_job(
            func=self._refresh_all,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="refresh_printers",
            name="Опрос принтеров",
            replace_existing=True,
            next_run_time=datetime.now(),
        )
        self.scheduler.start()
        logger.info(f"Планировщик запущен с интервалом {self.interval_minutes} мин.")

    def shutdown(self):
        self.scheduler.shutdown()