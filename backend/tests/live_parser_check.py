import sys
from src.printers.parsers import get_parser
from src.printers.parsers.pool import init_pool, get_pool

# Укажи реальные IP твоих принтеров для проверки
PRINTERS_TO_TEST = [
    {"vendor": "hp", "ip": "10.100.0.29"},
    {"vendor": "canon", "ip": "10.100.0.23"},
    {"vendor": "kyocera", "ip": "10.100.0.16"},
]

def main():
    print("Инициализация пула браузеров...")
    init_pool(max_drivers=3)

    for p in PRINTERS_TO_TEST:
        print(f"\n======================================")
        print(f"Опрос {p['vendor'].upper()} ({p['ip']})")
        print(f"======================================")

        parser = get_parser(p["vendor"], p["ip"])

        try:
            # Получаем чистые данные (словарь), которые генерирует парсер
            result = parser.get_status()
            print("РЕЗУЛЬТАТ:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Ошибка при опросе: {e}")

    # Очищаем пул, чтобы Chrome не висел в процессах
    print("\nОстановка пула...")
    get_pool().shutdown()

if __name__ == "__main__":
    main()