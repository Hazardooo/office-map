# src/printers/parsers/hp.py
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any

from src.printers.parsers.base import BasePrinterParser

class HPParser(BasePrinterParser):
    """Универсальный парсер для HP LaserJet. Ищет данные по всем возможным путям."""

    def get_status(self) -> Dict[str, Any]:
        # Список всех возможных путей, где HP хранит статус тонера
        urls_to_try = [
            f"http://{self.ip}/",  # Главная (часто делает редирект куда нужно)
            f"http://{self.ip}/hp/device/info_deviceStatus.html",
            f"http://{self.ip}/hp/device/this.html",
            f"http://{self.ip}/hp/device/supply_status.htm",
            f"http://{self.ip}/index.htm"
        ]

        toner_data = {}
        model = "HP LaserJet"
        hostname = "Unknown"

        # Общие заголовки, чтобы принтер не отбрасывал запросы
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=10, headers=headers)
                    if response.status_code != 200:
                        continue
                except requests.exceptions.RequestException:
                    continue  # Если таймаут или ошибка сети, пробуем следующий URL

                soup = BeautifulSoup(response.text, "html.parser")

                # 1. Поиск модели (учитываем неразрывные пробелы \xa0)
                title_tag = soup.find("title")
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    parts = title_text.split("\xa0")
                    if len(parts[0]) > 5:
                        model = parts[0].strip()

                # 2. Поиск Hostname
                user_id_div = soup.find("div", class_="userId")
                if user_id_div:
                    text = user_id_div.get_text(strip=True)
                    # HP часто разделяет имя, хост и IP длинными пробелами
                    segments = [s.strip() for s in re.split(r'\xa0{2,}', text) if s.strip()]
                    if len(segments) >= 3:
                        hostname = segments[1]
                    else:
                        hw_match = re.search(r'(NPI[A-Fa-f0-9]+|CN[A-Fa-f0-9]+|DEV[A-Fa-f0-9]+)', text, re.IGNORECASE)
                        if hw_match:
                            hostname = hw_match.group(1).upper()

                # 3. Парсинг тонера (Метод А: Графические индикаторы)
                for td in soup.find_all("td", style=True):
                    style = td.get("style", "").replace(" ", "").upper()
                    width_match = re.search(r'WIDTH:(\d+)%', style)
                    bg_match = re.search(r'BACKGROUND-COLOR:#([0-9A-F]{6})', style)

                    if width_match and bg_match:
                        hex_color = bg_match.group(1)
                        pct = width_match.group(1)

                        color_name = None
                        if hex_color == "000000": color_name = "Черный"
                        elif hex_color == "00FFFF": color_name = "Голубой"
                        elif hex_color == "FF00FF": color_name = "Пурпурный"
                        elif hex_color == "FFFF00": color_name = "Желтый"

                        if color_name and color_name not in toner_data:
                            toner_data[color_name] = f"{pct}%"

                # 3. Парсинг тонера (Метод Б: Текстовый поиск, если графики нет)
                if not toner_data:
                    target_colors = {
                        "черн": "Черный", "black": "Черный",
                        "голуб": "Голубой", "cyan": "Голубой",
                        "пурпур": "Пурпурный", "magenta": "Пурпурный",
                        "желт": "Желтый", "yellow": "Желтый"
                    }
                    for el in soup.find_all(["tr", "div"]):
                        row_text = el.get_text(" ", strip=True).lower()
                        # Ищем цифры или пустые значения '--' или '?'
                        pct_match = re.search(r'(\d+|--|\?)\s*%', row_text)

                        if pct_match:
                            val = pct_match.group(1)
                            val = "0" if val in ["--", "?"] else val
                            for trigger, rus_color in target_colors.items():
                                if trigger in row_text and rus_color not in toner_data:
                                    toner_data[rus_color] = f"{val}%"
                                    break

                # Если на текущей странице нашли данные тонера, дальше искать нет смысла
                if toner_data:
                    break

            if not toner_data:
                return {"error": "Уровень тонера не найден на странице"}

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except Exception as e:
            return {"error": f"Ошибка парсинга HP: {str(e)}"}