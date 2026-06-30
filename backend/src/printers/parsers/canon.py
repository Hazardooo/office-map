# src/printers/parsers/canon.py
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.pool import get_pool
from src.printers.parsers.exceptions import (
    ParserAuthError, ParserDOMError, ParserTimeoutError, ParserError
)

class CanonParser(BasePrinterParser):
    def _login_guest(self, driver) -> bool:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "radio2"))
            )
            driver.execute_script("document.getElementById('radio2').checked = true;")
            driver.execute_script("window.login();")
            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url.lower()
            )
            time.sleep(1.0)
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        pool = get_pool()
        driver = pool.acquire(timeout=25)

        try:
            driver.set_page_load_timeout(15)
            driver.set_script_timeout(15)

            try:
                driver.get(f"http://{self.ip}:8000/rps/portal.cgi")
            except TimeoutException:
                raise ParserTimeoutError(f"Таймаут подключения к порталу Canon ({self.ip}:8000)")

            if "login" in driver.current_url.lower():
                if not self._login_guest(driver):
                    raise ParserAuthError("Ошибка авторизации на портале Canon (порт 8000)")

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

            try:
                driver.get(f"http://{self.ip}")
            except TimeoutException:
                raise ParserTimeoutError(f"Таймаут подключения к корневой странице Canon ({self.ip})")

            if "login" in driver.current_url.lower():
                if not self._login_guest(driver):
                    raise ParserAuthError("Ошибка авторизации на корневой странице Canon")

            soup_toner = BeautifulSoup(driver.page_source, "html.parser")
            toner_data = {}

            toner_module = soup_toner.find("div", id="tonerInfomationModule")
            if toner_module:
                table = toner_module.find("table", class_="ItemListComponent")
                if table:
                    tbody = table.find("tbody")
                    if tbody:
                        for tr in tbody.find_all("tr"):
                            tds = tr.find_all(["th", "td"])
                            if len(tds) >= 2:
                                color = tds[0].get_text(strip=True)
                                percent_text = tds[1].get_text(strip=True)
                                match = re.search(r'(\d+)%', percent_text)
                                if match:
                                    toner_data[color] = f"{match.group(1)}%"

            if not toner_data:
                raise ParserDOMError("Блок тонера не найден. Возможно, изменилась прошивка принтера.")

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except (ParserAuthError, ParserDOMError, ParserTimeoutError) as e:
            raise e
        except Exception as e:
            raise ParserError(f"Неожиданная ошибка парсинга Canon: {str(e)}")
        finally:
            pool.release(driver)