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
    """Парсер Kyocera, который дает странице полностью прогрузиться перед сбором данных."""

    def __init__(self, ip: str):
        super().__init__(ip)
        self.base_url = f"https://{ip}"

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

            # Сбрасываем контекст фреймов
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

            # Открываем принтер (HTTPS -> HTTP)
            url_to_open = f"https://{self.ip}"
            try:
                driver.get(url_to_open)
            except TimeoutException:
                try: driver.execute_script("window.stop();")
                except Exception: pass
            except Exception as e:
                err_msg = str(e).lower()
                if any(x in err_msg for x in ["refused", "reset", "failed", "unreachable"]):
                    url_to_open = f"http://{self.ip}"
                    try:
                        driver.get(url_to_open)
                    except TimeoutException:
                        try: driver.execute_script("window.stop();")
                        except Exception: pass
                    except Exception as http_err:
                        return {"error": f"Принтер недоступен: {str(http_err)}"}

            # Ждем появления главного фрейма 'wlmframe' и заходим в него
            try:
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((By.NAME, "wlmframe"))
                )
            except TimeoutException:
                logger.debug(f"Фрейм wlmframe не найден на {self.ip}")

            # ==== ВОТ ОН, ТОТ САМЫЙ ХОД ====
            # Жестко спим 5 секунд. Даем тяжелому веб-интерфейсу Kyocera полностью
            # отрендерить Knockout.js, стянуть все скрипты и вставить цифры в DOM.
            time.sleep(5.0)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Парсим название модели
            model = "Kyocera ECOSYS"
            model_td = soup.find("td", id="info") or soup.find(id="wlm_01")
            if model_td:
                model_text = model_td.get_text(strip=True)
                if "Модель" in model_text and ":" in model_text:
                    model = model_text.split(":", 1)[1].strip()
                elif model_text:
                    model = model_text[:30]

            toner_data = {}

            # Ищем все строки (tr), где есть упоминания тонера/картриджей или знака %
            # на прогруженной странице внутри таблицы contentrow
            toner_table = soup.find("table", id="contentrow")
            if toner_table:
                # Мапа для определения цвета по фону полоски индикатора
                bgcolor_map = {
                    "#000000": "Черный",
                    "#0099ff": "Голубой",
                    "#ff0099": "Пурпурный",
                    "#ffff00": "Желтый"
                }

                for tr in toner_table.find_all("tr"):
                    tr_text = tr.get_text(" ", strip=True)
                    match = re.search(r'(\d+)%', tr_text)
                    if match:
                        percent_val = match.group(0)

                        # Метод 1: Ищем по цвету индикатора (самый точный)
                        has_color = False
                        for td in tr.find_all("td", bgcolor=True):
                            bg = td["bgcolor"].strip().lower()
                            if bg in bgcolor_map:
                                toner_data[bgcolor_map[bg]] = percent_val
                                has_color = True
                                break

                        # Метод 2: Если bgcolor нет, но в тексте строки написано имя цвета
                        if not has_color:
                            tr_text_lower = tr_text.lower()
                            if "black" in tr_text_lower or "чёрн" in tr_text_lower or "черн" in tr_text_lower:
                                toner_data["Черный"] = percent_val
                            elif "cyan" in tr_text_lower or "голуб" in tr_text_lower:
                                toner_data["Голубой"] = percent_val
                            elif "magenta" in tr_text_lower or "пурпур" in tr_text_lower:
                                toner_data["Пурпурный"] = percent_val
                            elif "yellow" in tr_text_lower or "желт" in tr_text_lower:
                                toner_data["Желтый"] = percent_val

            # Если таблица пустая, но страница точно прогрузилась (полный фолбэк)
            if not toner_data:
                all_pct = [f"{p}%" for p in re.findall(r'(\d+)%', soup.get_text()) if int(p) <= 100]
                if len(all_pct) >= 4:
                    toner_data["Черный"] = all_pct[0]
                    toner_data["Голубой"] = all_pct[1]
                    toner_data["Пурпурный"] = all_pct[2]
                    toner_data["Желтый"] = all_pct[3]
                elif all_pct:
                    toner_data["Черный"] = all_pct[0]

            # Если даже после 5 секунд сна пусто — возвращаем ошибку, чтобы ты видел проблему
            if not toner_data:
                return {"error": "Не удалось найти данные тонера после полной загрузки страницы"}

            return {
                "model": model,
                "hostname": "Unknown",
                "toner": toner_data
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга Kyocera ({self.ip}): {str(e)}")
            return {"error": f"Ошибка парсинга Kyocera: {str(e)}"}
        finally:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            pool.release(driver)