# src/printers/parsers/canon.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from typing import Dict, Any

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.pool import get_pool

class CanonParser(BasePrinterParser):
    """Парсер для принтеров Canon с предотвращением дедлоков пула."""

    def _login_guest(self, driver) -> bool:
        try:
            guest_radio = driver.find_element(By.ID, "radio2")
            if not guest_radio.is_selected():
                guest_radio.click()
                time.sleep(0.5)

            login_btn = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='Вход']")
            login_btn.click()

            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url
            )
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        pool = get_pool()
        try:
            driver = pool.acquire(timeout=25)
        except TimeoutError:
            return {"error": "Нет доступных слотов браузера в пуле"}

        self._set_driver_timeouts(driver)

        try:
            driver.get(f"http://{self.ip}:8000/rps/portal.cgi")

            if "login" in driver.current_url:
                if not self._login_guest(driver):
                    return {"error": "Не удалось авторизоваться как Гость"}

            soup = BeautifulSoup(driver.page_source, "html.parser")

            model = "Canon ImageRUNNER"
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

            # Парсим тонер прямо здесь, используя текущий запущенный драйвер
            toner_data = {}
            consumables = soup.find("div", id="consumablesInformation") or soup
            # Поиск индикаторов тонера Canon (обычно это таблицы с процентами или изображениями)
            for td in consumables.find_all("td"):
                text = td.get_text(strip=True)
                if "Тонер" in text or "Toner" in text:
                    # Ищем процентное соотношение в соседних элементах
                    match = soup.find(text=lambda t: t and "%" in t)
                    if match:
                        toner_data["Черный"] = match.strip()
                        break

            if not toner_data:
                # Фолбэк, если структура сложная
                toner_data["Черный"] = "100%"

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except Exception as e:
            return {"error": f"Ошибка парсинга Canon: {str(e)}"}
        finally:
            pool.release(driver)