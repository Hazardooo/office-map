from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from typing import Dict, Any

from src.printers.parsers.base import BasePrinterParser
from src.printers.parsers.pool import get_pool

class CanonParser(BasePrinterParser):
    """Парсер для принтеров Canon с безопасным управлением пулом браузеров."""

    def _login_guest(self, driver) -> bool:
        """Проходит форму авторизации."""
        try:
            # Ждем появления радиокнопки
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "radio2"))
            )

            # Выбираем "Режим конечного пользователя" через JS (надежнее клика)
            driver.execute_script("document.getElementById('radio2').checked = true;")

            # Вызываем нативную функцию входа, не привязываясь к языку слова "Вход"
            driver.execute_script("window.login();")

            # Ждем редиректа
            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url.lower()
            )
            time.sleep(1.0) # Небольшая пауза для отрисовки DOM
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        pool = get_pool()
        # Берем ТОЛЬКО ОДИН драйвер для всего процесса
        driver = pool.acquire(timeout=25)
        if not driver:
            return {"error": "Нет доступных драйверов в пуле"}

        try:
            driver.set_page_load_timeout(15)
            driver.set_script_timeout(15)

            # --- ШАГ 1: Идем на порт 8000 за моделью и хостнеймом ---
            driver.get(f"http://{self.ip}:8000/rps/portal.cgi")

            if "login" in driver.current_url.lower():
                if not self._login_guest(driver):
                    return {"error": "Ошибка входа на портал (порт 8000)"}

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

            # --- ШАГ 2: В ЭТОМ ЖЕ БРАУЗЕРЕ идем на корень (порт 80) за тонером ---
            driver.get(f"http://{self.ip}")

            # На всякий случай проверяем, не требует ли корень тоже логина
            if "login" in driver.current_url.lower():
                if not self._login_guest(driver):
                    return {"error": "Ошибка входа на корневую страницу"}

            soup_toner = BeautifulSoup(driver.page_source, "html.parser")
            toner_data = {}

            # Твои точные селекторы из старого кода
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
                return {"error": "Блок тонера не найден на корневой странице"}

            return {
                "model": model,
                "hostname": hostname,
                "toner": toner_data
            }

        except Exception as e:
            return {"error": f"Ошибка парсинга Canon: {str(e)}"}
        finally:
            # Обязательно отдаем драйвер обратно
            pool.release(driver)