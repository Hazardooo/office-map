# run_real_test.py
import asyncio
import inspect
import sys
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Импорты твоих модулей проекта
from src.database import Base
from src.printers import schemas, models
from src.printers.service import PrinterService
from src.settings import settings
from src.printers.parsers import get_parser
# Импортируем инициализацию пула и сам парсер для диагностики
try:
    from src.printers.parsers.pool import init_pool
except ImportError:
    print(
        "ОШИБКА: Не удалось импортировать init_pool или get_parser. "
        "Проверь правильность пути к src.printers.parsers!",
        file=sys.stderr
    )
    raise

# TODO: Укажи здесь свою реальную строку подключения к DEV-базе данных
DATABASE_URL = settings.POSTGRES_URL


async def main():
    print("==================================================")
    print("=== ШАГ 0: Инициализация сетевого пула ===")
    print("==================================================")
    try:
        if inspect.iscoroutinefunction(init_pool):
            await init_pool()
        else:
            init_pool()
        print("Пул соединений успешно инициализирован.")
    except Exception as e:
        print(f"Не удалось инициализировать пул: {e}", file=sys.stderr)
        return

    print("\n==================================================")
    print("=== ДИАГНОСТИКА: Прямой опрос парсера ===")
    print("==================================================")
    try:
        print("Создаем парсер для kyocera (10.100.0.34)...")
        test_parser = get_parser("kyocera", "10.100.0.34")

        start_time = time.time()
        print("Вызываем синхронный метод get_status() напрямую...")
        raw_status = test_parser.get_status()

        print(f"Парсер успешно ответил напрямую за {time.time() - start_time:.2f} сек!")
        print(f"Сырые данные от принтера:\n{raw_status}")
    except Exception as pe:
        print("\n[!] ОШИБКА ПРИ ПРЯМОМ ОПРОСЕ ПАРСЕРА:")
        import traceback
        traceback.print_exc()
        print("==================================================\n")
        print("Останавливаем скрипт, так как парсер вернул ошибку.", file=sys.stderr)
        return

    print("\n==================================================")
    print("=== ШАГ 1: Проверка и создание таблиц в БД ===")
    print("==================================================")
    engine = create_async_engine(DATABASE_URL, echo=False)  # Поставь True, если хочешь видеть SQL-логи
    async_session_local = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        print("Проверяем структуру БД и создаем таблицу 'printers', если её нет...")
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы проверены.")

    # Входящие данные для реального принтера
    printer_data = schemas.PrinterCreate(
        ip="10.100.0.34",
        vendor="kyocera",
        x=12.5,
        y=45.0,
        name="Руководство"
    )

    print(f"\n==================================================")
    print(f"=== ШАГ 2: Тестирование PrinterService.create() ===")
    print(f"==================================================")
    print(f"Отправляем запрос на создание принтера {printer_data.ip}...")

    async with async_session_local() as session:
        service = PrinterService(db=session)

        try:
            created_printer = await service.create(printer_data)

            print("\n[ЗАПИСЬ В БД УСПЕШНА]")
            print(f" -> ID в базе: {created_printer.id}")
            print(f" -> Имя: {created_printer.name}")
            print(f" -> Модель: {created_printer.model}")
            print(f" -> Серийный номер: {created_printer.serial_number}")
            print(f" -> Статус сетевой доступности: {created_printer.is_online}")
            print(f" -> Остаток черного тонера: {created_printer.toner_black}%")

        except Exception as e:
            print(f"\n[!] ОШИБКА внутри PrinterService.create(): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            await session.rollback()
            return

    print("\n==================================================")
    print("=== ШАГ 3: Проверка чтения (PrinterService.get_all) ===")
    print("==================================================")
    async with async_session_local() as session:
        service = PrinterService(db=session)
        all_printers = await service.get_all()

        print(f"Успешно вычитали данные. Всего принтеров в вашей базе: {len(all_printers)}")
        for p in all_printers:
            if p.ip == "10.100.0.34":
                print(f" -> Подтверждено в БД: {p.name} [{p.ip}] (Модель: {p.model})")

    print("\nТестирование завершено успешно!")


if __name__ == "__main__":
    # Запуск асинхронного event loop
    asyncio.run(main())