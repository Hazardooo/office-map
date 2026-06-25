# src/printers/parsers/hp.py
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any

from src.printers.parsers.base import BasePrinterParser

class HPParser(BasePrinterParser):
    """Универсальный парсер для HP LaserJet с жесткими сетевыми таймаутами."""

    COLOR_MAP = {
        "черн": "Черный",
        "black": "Черный",
        "голуб": "Голубой",
        "cyan": "Голубой",
        "пурпур": "Пурпурный",
        "magenta": "Пурпурный",
        "желт": "Желтый",
        "yellow": "Желтый",
    }

    def get_status(self) -> Dict[str, Any]:
        url = f"http://{self.ip}/hp/device/this.html"
        try:
            # Защита от зависания: ставим таймаут 15 секунд на соединение и чтение данных
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                # Пробуем альтернативный путь для старых моделей HP
                url = f"http://{self.ip}/index.htm"
                response = requests.get(url, timeout=15)

            soup = BeautifulSoup(response.text, "html.parser")

            # Поиск модели
            model = "HP LaserJet"
            title_tag = soup.find("title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                parts = title_text.split(" - ")
                model = parts[0].strip() if parts else title_text

            # Поиск Hostname
            hostname = "Unknown"
            user_id_div = soup.find("div", class_="userId")
            if user_id_div:
                text = user_id_div.get_text(strip=True)
                hw_match = re.search(r'(NPI[A-Fa-f0-9]+|CN[A-Fa-f0-9]+|DEV[A-Fa-f0-9]+)', text, re.IGNORECASE)
                if hw_match:
                    hostname = hw_match.group(1).upper()

            # Сбор информации о тонерах
            toner_data = {}
            # Пример парсинга стандартных блоков поставок HP
            for supply_div in soup.find_all(["div", "td"], class_=re.compile(re.escape("supply"), re.IGNORECASE)):
                text = supply_div.get_text(strip=True).lower()
                for key, rus_color in self.COLOR_MAP.items():
                    if key in text:
                        percent_match = re.search(r'(\d+)%', text)
                        if percent_match:
                            toner_data[rus_color] = f"{percent_match.group(1)}%"

            if not toner_data:
                # Фолбэк парсинга по текстовым вхождениям на странице
                all_text = soup.get_text()
                match = re.search(r'(?:Остаток|Картридж).*?(\d+)%', all_text, re.IGNORECASE)
                toner_data["Черный"] = f"{match.group(1)}%" if match else "100%"

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"HP принтер недоступен по сети: {str(e)}"}
        except Exception as e:
            return {"error": f"Ошибка парсинга HP: {str(e)}"}