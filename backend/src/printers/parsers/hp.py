# src/printers/parsers/hp.py
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.exceptions import ParserDOMError, ParserTimeoutError, ParserError

class HPParser(BasePrinterParser):
    def get_status(self) -> Dict[str, Any]:
        urls_to_try = [
            f"http://{self.ip}/",
            f"http://{self.ip}/hp/device/info_deviceStatus.html",
            f"http://{self.ip}/hp/device/this.html",
            f"http://{self.ip}/hp/device/supply_status.htm",
            f"http://{self.ip}/index.htm"
        ]

        toner_data = {}
        model = "HP LaserJet"
        hostname = "Unknown"
        success_responses = 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=10, headers=headers)
                    if response.status_code == 200:
                        success_responses += 1
                    else:
                        continue
                except requests.exceptions.RequestException:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                title_tag = soup.find("title")
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    parts = title_text.split("\xa0")
                    if len(parts[0]) > 5:
                        model = parts[0].strip()

                user_id_div = soup.find("div", class_="userId")
                if user_id_div:
                    text = user_id_div.get_text(strip=True)
                    segments = [s.strip() for s in re.split(r'\xa0{2,}', text) if s.strip()]
                    if len(segments) >= 3:
                        hostname = segments[1]
                    else:
                        hw_match = re.search(r'(NPI[A-Fa-f0-9]+|CN[A-Fa-f0-9]+|DEV[A-Fa-f0-9]+)', text, re.IGNORECASE)
                        if hw_match:
                            hostname = hw_match.group(1).upper()

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

                if not toner_data:
                    target_colors = {
                        "черн": "Черный", "black": "Черный",
                        "голуб": "Голубой", "cyan": "Голубой",
                        "пурпур": "Пурпурный", "magenta": "Пурпурный",
                        "желт": "Желтый", "yellow": "Желтый"
                    }
                    for el in soup.find_all(["tr", "div"]):
                        row_text = el.get_text(" ", strip=True).lower()
                        pct_match = re.search(r'(\d+|--|\?)\s*%', row_text)

                        if pct_match:
                            val = pct_match.group(1)
                            val = "0" if val in ["--", "?"] else val
                            for trigger, rus_color in target_colors.items():
                                if trigger in row_text and rus_color not in toner_data:
                                    toner_data[rus_color] = f"{val}%"
                                    break

                if toner_data:
                    break

            if not toner_data:
                if success_responses == 0:
                    raise ParserTimeoutError(f"HP {self.ip} не ответил ни по одному из известных URL")
                else:
                    raise ParserDOMError(f"Уровень тонера не найден на страницах HP {self.ip}")

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except (ParserDOMError, ParserTimeoutError) as e:
            raise e
        except Exception as e:
            raise ParserError(f"Неожиданная ошибка парсинга HP: {str(e)}")