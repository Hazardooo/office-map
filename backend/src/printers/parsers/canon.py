from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from typing import Dict

from .base import BasePrinterParser
from .pool import get_pool


class CanonParser(BasePrinterParser):
    """Парсер для принтеров Canon с пулом драйверов."""

    def _login_guest(self, driver) -> bool:
        try:
            guest_radio = driver.find_element(By.ID, "radio2")
            if not guest_radio.is_selected():
                guest_radio.click()
                time.sleep(0.5)

            login_btn = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='Вход']")
            login_btn.click()

            # Ждём редиректа вместо фиксированного sleep
            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url
            )
            return True
        except Exception as e:
            return False

    def get_toner(self) -> Dict[str, str]:
        pool = get_pool()
        driver = pool.acquire(timeout=15)
        if not driver:
            return {"error": "Нет доступных драйверов в пуле"}

        try:
            driver.get(f"http://{self.ip}")

            if "login" in driver.current_url:
                if not self._login_guest(driver):
                    return {"error": "Ошибка входа"}

            # Уменьшаем sleep, используем WebDriverWait
            soup = BeautifulSoup(driver.page_source, "html.parser")

            toner_module = soup.find("div", id="tonerInfomationModule")
            if not toner_module:
                return {"error": "Блок тонера не найден"}

            table = toner_module.find("table", class_="ItemListComponent")
            if not table:
                return {"error": "Таблица тонера не найдена"}

            result = {}
            tbody = table.find("tbody")
            if tbody:
                for tr in tbody.find_all("tr"):
                    tds = tr.find_all(["th", "td"])
                    if len(tds) >= 2:
                        color = tds[0].get_text(strip=True)
                        percent_text = tds[1].get_text(strip=True)
                        match = re.search(r'(\d+%)', percent_text)
                        if match:
                            result[color] = match.group(1)

            return result if result else {"error": "Данные не найдены"}

        except Exception as e:
            return {"error": str(e)}
        finally:
            pool.release(driver)

    def get_status(self) -> Dict[str, str]:
        pool = get_pool()
        driver = pool.acquire(timeout=15)
        if not driver:
            return {"error": "Нет доступных драйверов"}

        try:
            driver.get(f"http://{self.ip}:8000/rps/portal.cgi")

            if "login" in driver.current_url:
                if not self._login_guest(driver):
                    return {"error": "Ошибка входа"}

            soup = BeautifulSoup(driver.page_source, "html.parser")

            model = "Unknown"
            hostname = "Unknown"

            product_info = soup.find("div", id="productInformation")
            if product_info:
                for tr in product_info.find_all("tr"):
                    th = tr.find("th")
                    td = tr.find("td")
                    if th and td:
                        label = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        if "Имя устройства" in label:
                            hostname = value
                        elif "Наименование изделия" in label:
                            model = value

            toner = self.get_toner()
            if "error" in toner:
                return toner

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            pool.release(driver)