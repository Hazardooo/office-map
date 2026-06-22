import asyncio
import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.database import AsyncSessionLocal
from src.printers.service import PrinterService
from src.printers import models
from src.printers.parsers.pool import init_pool, shutdown_pool

logger = logging.getLogger(__name__)


class PrinterScheduler:
    def __init__(self, interval_minutes: int = 5, max_concurrent: int = 5, pool_size: int = 3):
        self.scheduler = AsyncIOScheduler()
        self.interval_minutes = interval_minutes
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.pool_size = pool_size

    async def _refresh_all(self):
        """Опрос всех принтеров и обновление БД."""
        async with AsyncSessionLocal() as session:
            service = PrinterService(session)
            printers: List[models.Printer] = await service.get_all()

        if not printers:
            logger.info("Нет принтеров для опроса")
            return

        logger.info(f"Начинаю опрос {len(printers)} принтеров (max {self.semaphore._value} одновременно)...")

        tasks = [self._refresh_single(p) for p in printers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False)
        errors = [r for r in results if isinstance(r, Exception)]

        logger.info(f"Опрос завершён: {success} успешно, {failed} ошибок")
        for e in errors:
            logger.error(f"Исключение: {e}")

    async def _refresh_single(self, printer: models.Printer) -> bool:
        """Каждый принтер — изолированная сессия + ограничение concurrency."""
        async with self.semaphore:
            async with AsyncSessionLocal() as session:
                service = PrinterService(session)
                try:
                    await service.refresh(printer.id)
                    logger.debug(f"✅ {printer.ip} — обновлён")
                    return True
                except Exception as e:
                    logger.warning(f"❌ {printer.ip} — {e}")
                    return False

    def start(self):
        # Инициализируем пул драйверов
        init_pool(max_drivers=self.pool_size)
        logger.info(f"Пул Selenium: {self.pool_size} драйверов")

        self.scheduler.add_job(
            func=self._refresh_all,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="refresh_printers",
            name="Опрос принтеров",
            replace_existing=True,
            next_run_time=datetime.now(),
        )
        self.scheduler.start()
        logger.info(f"Планировщик запущен: интервал {self.interval_minutes} мин")

    def shutdown(self):
        self.scheduler.shutdown()
        shutdown_pool()
        logger.info("Планировщик и пул остановлены")