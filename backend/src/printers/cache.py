# src/printers/cache.py
import json
from redis.asyncio import Redis
from src.printers.repository import PrinterRepository
from src.printers.schemas import PrinterResponse

class CachedPrinterRepository:
    def __init__(self, repo: PrinterRepository, cache: Redis):
        self.repo = repo
        self.cache = cache
        self.TTL = 300  # 5 минут

    async def get_all(self):
        # 1. Пробуем достать из кэша
        cached = await self.cache.get("all_printers")
        if cached:
            data = json.loads(cached)
            # Десериализуем обратно в Pydantic-модели.
            # Это позволяет обращаться к ним как p.id, p.ip (как ожидает планировщик)
            return [PrinterResponse(**item) for item in data]

        # 2. Если кэш пуст — идем в БД
        printers = await self.repo.get_all()

        # 3. Сериализуем объекты БД с помощью Pydantic (он сам переведет UUID в строки)
        json_data = [PrinterResponse.model_validate(p).model_dump(mode='json') for p in printers]
        await self.cache.setex("all_printers", self.TTL, json.dumps(json_data))

        return printers

    # =========================================================
    # МУТИРУЮЩИЕ МЕТОДЫ (все они должны инвалидировать кэш)
    # =========================================================

    async def refresh_toner(self, printer, parsed):
        result = await self.repo.refresh_toner(printer, parsed)
        await self.cache.delete("all_printers")
        return result

    async def set_offline(self, printer):
        result = await self.repo.set_offline(printer)
        await self.cache.delete("all_printers")
        return result

    async def update(self, printer, data):
        result = await self.repo.update(printer, data)
        await self.cache.delete("all_printers")
        return result

    async def create(self, data, parsed=None):
        # На случай если сигнатура create отличается
        if parsed:
            result = await self.repo.create(data, parsed)
        else:
            result = await self.repo.create(data)

        await self.cache.delete("all_printers")
        return result

    async def delete(self, printer):
        if hasattr(self.repo, 'delete'):
            result = await self.repo.delete(printer)
            await self.cache.delete("all_printers")
            return result

    # =========================================================
    # ДЕЛЕГИРОВАНИЕ (для методов чтения, например get_by_id)
    # =========================================================
    def __getattr__(self, name):
        return getattr(self.repo, name)