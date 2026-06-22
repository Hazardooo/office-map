from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from typing import Dict

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.pool import get_pool


class KyoceraParser(BasePrinterParser):
    """Парсер для принтеров Kyocera с пулом драйверов."""

    def get_toner(self) -> Dict[str, str]:
        pool = get_pool()
        driver = pool.acquire(timeout=15)
        if not driver:
            return {"error": "Нет доступных драйверов"}

        try:
            driver.get(f"{self.base_url}/wlmpor/index.htm")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "wlmframe"))
            )
            driver.switch_to.frame("wlmframe")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "toner"))
            )
            driver.switch_to.frame("toner")

            soup = BeautifulSoup(driver.page_source, "html.parser")
            toner_table = soup.find("table", id="contentrow")

            if not toner_table:
                return {"error": "Таблица тонера не найдена"}

            result = {}
            for tr in toner_table.find_all("tr"):
                tds = tr.find_all("td")
                row_data = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]

                color = None
                percent = None
                for text in row_data:
                    if text in ["Черный", "Голубой", "Пурпурный", "Желтый",
                                "Black", "Cyan", "Magenta", "Yellow"]:
                        color = text
                    if "%" in text:
                        percent = text

                if color and percent:
                    result[color] = percent

            return result if result else {"error": "Данные не найдены"}

        except Exception as e:
            return {"error": str(e)}
        finally:
            # Возвращаемся к основному окну перед освобождением
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            pool.release(driver)

    def get_status(self) -> Dict[str, str]:
        toner = self.get_toner()
        if "error" in toner:
            return toner
        return {
            "model": "ECOSYS P3060dn",
            "hostname": "Unknown",
            "toner": toner
        }