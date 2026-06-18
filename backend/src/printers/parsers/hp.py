# parsers/hp.py
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict

from .base import BasePrinterParser


class HPParser(BasePrinterParser):
    """Парсер для принтеров HP."""

    def get_toner(self) -> Dict[str, str]:
        try:
            url = f"http://{self.ip}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Ищем секцию "Сведения о расходных материалах"
            # По заголовку h3 с классом subTitle
            result = {}

            # Находим все таблицы с классом mainContentArea
            tables = soup.find_all("table", class_="mainContentArea")

            for table in tables:
                # Ищем строки с данными о картридже
                for tr in table.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) >= 2:
                        # Первая ячейка — название картриджа
                        name_cell = tds[0]
                        name_text = name_cell.get_text(strip=True)

                        # Ищем цвет в названии
                        color = None
                        if "Черный" in name_text or "Black" in name_text:
                            color = "Черный"
                        elif "Голубой" in name_text or "Cyan" in name_text:
                            color = "Голубой"
                        elif "Пурпурный" in name_text or "Magenta" in name_text:
                            color = "Пурпурный"
                        elif "Желтый" in name_text or "Yellow" in name_text:
                            color = "Желтый"

                        # Вторая ячейка с процентом (alignRight)
                        percent_cell = None
                        for td in tds:
                            if "alignRight" in str(td.get("class", [])):
                                percent_cell = td
                                break

                        if color and percent_cell:
                            percent_text = percent_cell.get_text(strip=True)
                            match = re.search(r'(\d+)%', percent_text)
                            if match:
                                result[color] = f"{match.group(1)}%"

            # Альтернативный поиск — по ширине полосы тонера
            if not result:
                for td in soup.find_all("td"):
                    style = td.get("style", "")
                    if "BACKGROUND-COLOR: #000000" in style or "BACKGROUND-COLOR: black" in style:
                        # Ищем соседнюю ячейку с процентом
                        width_match = re.search(r'WIDTH:(\d+)%', style)
                        if width_match:
                            percent = width_match.group(1)
                            # Ищем цвет рядом
                            parent = td.find_parent("tr")
                            if parent:
                                for sibling in parent.find_all("td"):
                                    text = sibling.get_text(strip=True)
                                    if "Черный" in text:
                                        result["Черный"] = f"{percent}%"
                                        break

            return result if result else {"error": "Данные о тонере не найдены"}

        except requests.RequestException as e:
            return {"error": f"Ошибка запроса: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def get_status(self) -> Dict[str, str]:
        try:
            url = f"http://{self.ip}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Модель принтера
            model = "Unknown"
            title = soup.find("title")
            if title:
                model = title.get_text(strip=True).split("&nbsp;")[0]

            # Имя устройства (NPI...)
            hostname = "Unknown"
            user_id_div = soup.find("div", class_="userId")
            if user_id_div:
                parts = user_id_div.get_text(strip=True).split()
                for part in parts:
                    if part.startswith("NPI") or part.startswith("CN"):
                        hostname = part
                        break

            # Статус устройства
            status = "Unknown"
            status_cell = soup.find("td", id="deviceStatus_tableCell")
            if status_cell:
                status = status_cell.get_text(strip=True)

            toner = self.get_toner()
            if "error" in toner:
                return toner

            return {
                "model": model,
                "hostname": hostname,
                "status": status,
                "toner": toner
            }

        except Exception as e:
            return {"error": str(e)}