# src/printers/parsers/kyocera.py
import logging
import re
import time
from typing import Any, Dict
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.pool import get_pool

logger = logging.getLogger(__name__)

class KyoceraParser(BasePrinterParser):
    """Парсер Kyocera (HTTP), извлекающий данные из вложенных фреймов wlmframe -> toner."""

    def __init__(self, ip: str):
        super().__init__(ip)
        self.base_url = f"http://{ip}"

    def get_toner(self) -> Dict[str, str]:
        status = self.get_status()
        return status.get("toner", status)

    def get_status(self) -> Dict[str, Any]:
        pool = get_pool()
        try:
            driver = pool.acquire(timeout=25)
        except Exception:
            return {"error": "Нет доступных слотов в пуле браузеров"}

        try:
            driver.set_page_load_timeout(15)
            driver.set_script_timeout(15)

            try:
                driver.switch_to.default_content()
            except Exception:
                pass

            try:
                driver.get(self.base_url)
            except TimeoutException:
                try: driver.execute_script("window.stop();")
                except Exception: pass
            except Exception as http_err:
                return {"error": f"Принтер недоступен: {str(http_err)}"}

            # Шаг 1: Заходим в главный фрейм
            try:
                WebDriverWait(driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.NAME, "wlmframe"))
                )
            except TimeoutException:
                return {"error": "Главный фрейм 'wlmframe' не найден"}

            # Ждем рендеринг JS
            time.sleep(4.0)

            soup_main = BeautifulSoup(driver.page_source, "html.parser")
            model = "Kyocera ECOSYS"
            hostname = "Unknown"

            # Парсинг метаданных (согласно дампу, они лежат в <td id="info">)
            infos = soup_main.find_all("td", id="info")
            for info in infos:
                text = info.get_text(strip=True)
                if "Модель :" in text:
                    model = text.split("Модель :")[-1].strip()
                elif "Имя хоста :" in text:
                    hostname = text.split("Имя хоста :")[-1].strip()

            # Шаг 2: Заходим во вложенный фрейм 'toner'
            try:
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "toner"))
                )
            except TimeoutException:
                return {"error": "Не удалось найти вложенный фрейм 'toner'"}

            # Парсинг тонера (согласно дампу, таблица id="contentrow")
            soup_toner = BeautifulSoup(driver.page_source, "html.parser")
            toner_data = {}

            toner_table = soup_toner.find("table", id="contentrow")
            if toner_table:
                target_colors = {
                    "Черный": "Черный", "Black": "Черный",
                    "Голубой": "Голубой", "Cyan": "Голубой",
                    "Пурпурный": "Пурпурный", "Magenta": "Пурпурный",
                    "Желтый": "Желтый", "Yellow": "Желтый"
                }

                for tr in toner_table.find_all("tr"):
                    row_text = tr.get_text(" ", strip=True)
                    pct_match = re.search(r'(\d+)\s*%', row_text)

                    if pct_match:
                        for trigger, rus_color in target_colors.items():
                            if trigger in row_text and rus_color not in toner_data:
                                toner_data[rus_color] = f"{pct_match.group(1)}%"
                                break

            if not toner_data:
                return {"error": "Не удалось извлечь данные тонера из таблицы фрейма"}

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга Kyocera ({self.ip}): {str(e)}")
            return {"error": f"Ошибка: {str(e)}"}
        finally:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            pool.release(driver)