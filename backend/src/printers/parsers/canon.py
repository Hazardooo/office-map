from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
from typing import Dict

from .base import BasePrinterParser


CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")


class CanonParser(BasePrinterParser):
    """Парсер для принтеров Canon."""

    def _login_guest(self, driver) -> bool:
        """Вход в режиме конечного пользователя (без пароля)."""
        try:
            # Убеждаемся, что выбран "Режим конечного пользователя"
            guest_radio = driver.find_element(By.ID, "radio2")
            if not guest_radio.is_selected():
                guest_radio.click()
                time.sleep(1)

            # Кликаем "Вход"
            login_btn = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='Вход']")
            login_btn.click()
            time.sleep(5)

            return True
        except Exception as e:
            print(f"Guest login error: {e}")
            return False

    def get_toner(self) -> Dict[str, str]:
        driver = None
        try:
            driver = webdriver.Chrome(options=CHROME_OPTIONS)
            url = f"http://{self.ip}"
            driver.get(url)
            time.sleep(3)

            # Проверяем, нужна ли авторизация
            if "login" in driver.current_url or "Имя для входа" in driver.page_source:
                if not self._login_guest(driver):
                    return {"error": "Ошибка входа в режиме гостя"}

            # Парсим страницу портала
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

            return result if result else {"error": "Данные о тонере не найдены"}

        except Exception as e:
            return {"error": str(e)}
        finally:
            if driver:
                driver.quit()

    def get_status(self) -> Dict[str, str]:
        driver = None
        try:
            driver = webdriver.Chrome(options=CHROME_OPTIONS)
            url = f"http://{self.ip}:8000/rps/portal.cgi"
            driver.get(url)
            time.sleep(3)

            if "login" in driver.current_url or "Имя для входа" in driver.page_source:
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
            if driver:
                driver.quit()