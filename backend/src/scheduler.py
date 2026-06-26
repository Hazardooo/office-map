import asyncio
import logging
from datetime import datetime
from typing import List

# ИСПРАВЛЕНИЕ 1: Импортируем именно асинхронную версию redis
import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.database.postgres import AsyncSessionLocal
from src.printers import models
from src.printers.cache import CachedPrinterRepository
from src.printers.parsers.pool import init_pool
from src.printers.repository import PrinterRepository
from src.printers.service import PrinterService
from src.settings import settings

logger = logging.getLogger(__name__)


class PrinterScheduler:
    def __init__(self, interval_minutes: int = 5, max_concurrent: int = 5, pool_size: int = 4):
        self.scheduler = AsyncIOScheduler()
        self.interval_minutes = interval_minutes
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.pool_size = pool_size

    async def _refresh_all(self):
        """
        Метод опроса принтеров.
        Собираем цепочку: Session -> RawRepo -> CachedRepo -> Service
        """
        logger.info("Запуск фонового обновления принтеров...")

        try:
            # ИСПРАВЛЕНИЕ 2: Открываем Redis ДО открытия сессии БД
            redis_client = await redis.from_url(settings.DRAGONFLY_URL, decode_responses=True)
            try:
                # ИСПРАВЛЕНИЕ 3: Убрано дублирование контекстного менеджера AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    raw_repo = PrinterRepository(session)
                    cached_repo = CachedPrinterRepository(raw_repo, redis_client)
                    service = PrinterService(cached_repo)

                    # ИСПРАВЛЕНИЕ 4: Теперь операции выполняются ДО закрытия redis_client
                    printers: List[models.Printer] = await service.get_all()

                    logger.info(f"Найдено {len(printers)} принтеров для обновления.")

                    for printer in printers:
                        try:
                            await service.refresh(printer.id)
                        except Exception as e:
                            logger.error(f"Ошибка обновления принтера {printer.ip}: {e}")
                    logger.info("Прогрев кэша после обновления...")
                    await service.get_all()
                    logger.info("Фоновое обновление завершено.")
            finally:
                # Закрываем Redis ТОЛЬКО когда все принтеры обновились
                await redis_client.close()

        except Exception as e:
            logger.error(f"Критическая ошибка в планировщике: {e}")

    async def _refresh_single(self, printer_id, printer_ip: str) -> bool:
        """Каждый принтер — изолированная сессия + ограничение concurrency."""
        async with self.semaphore:
            try:
                # ИСПРАВЛЕНИЕ 5: Приводим _refresh_single к новой архитектуре с кэшем
                redis_client = await redis.from_url(settings.DRAGONFLY_URL, decode_responses=True)
                try:
                    async with AsyncSessionLocal() as session:
                        raw_repo = PrinterRepository(session)
                        cached_repo = CachedPrinterRepository(raw_repo, redis_client)
                        service = PrinterService(cached_repo)

                        # Сервис выполняет парсинг по ID
                        updated_printer = await service.refresh(printer_id)

                        # Проверяем статус через возвращенный из свежей сессии объект
                        if updated_printer and not updated_printer.is_online:
                            logger.warning(f"❌ Принтер {printer_ip} не обновился (переведен в offline из-за ошибки)")
                            return False

                        logger.info(f"✅ Принтер {printer_ip} успешно обновлен планировщиком.")
                        return True
                finally:
                    await redis_client.close()
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
