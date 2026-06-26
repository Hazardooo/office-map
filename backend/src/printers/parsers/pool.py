# src/printers/parsers/pool.py
import threading
import logging
import time
from typing import Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.printers.parsers.exceptions import PoolTimeoutError

logger = logging.getLogger(__name__)

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless=new")
CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_OPTIONS.add_argument("--disable-gpu")
CHROME_OPTIONS.add_argument("--disable-extensions")
CHROME_OPTIONS.add_argument("--disable-plugins")
CHROME_OPTIONS.add_argument("--disable-images")
CHROME_OPTIONS.add_argument("--blink-settings=imagesEnabled=false")
CHROME_OPTIONS.add_argument("--window-size=1280,720")
CHROME_OPTIONS.page_load_strategy = 'eager'
CHROME_OPTIONS.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.default_content_setting_values.notifications": 2,
})
CHROME_OPTIONS.add_experimental_option("excludeSwitches", ["enable-logging"])

class DriverPool:
    def __init__(self, max_drivers: int = 3, max_usage: int = 50):
        self.max_drivers = max_drivers
        self.max_usage = max_usage
        self._available: List[webdriver.Chrome] = []
        self._in_use: List[webdriver.Chrome] = []
        self._driver_usage: Dict[int, int] = {}
        self._condition = threading.Condition()
        self._shutdown = False

        for _ in range(self.max_drivers):
            driver = self._create_driver()
            self._available.append(driver)

    def _create_driver(self) -> webdriver.Chrome:
        driver = webdriver.Chrome(options=CHROME_OPTIONS)
        self._driver_usage[id(driver)] = 0
        return driver

    def acquire(self, timeout: float = 30.0) -> webdriver.Chrome:
        start_time = time.time()
        with self._condition:
            while not self._available:
                if self._shutdown:
                    raise RuntimeError("Пул драйверов уже остановлен")

                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    # ВЫБРАСЫВАЕМ НАШУ ОШИБКУ
                    raise PoolTimeoutError(f"Превышено время ожидания свободного драйвера ({timeout} сек)")

                self._condition.wait(timeout=remaining)

            driver = self._available.pop(0)
            self._in_use.append(driver)
            return driver

    def release(self, driver: webdriver.Chrome) -> None:
        with self._condition:
            if driver in self._in_use:
                self._in_use.remove(driver)

                if self._shutdown:
                    try: driver.quit()
                    except Exception: pass
                    return

                d_id = id(driver)
                self._driver_usage[d_id] += 1

                if self._driver_usage[d_id] >= self.max_usage:
                    logger.info(f"Перезапуск процесса Chrome {d_id} из-за лимита ({self.max_usage})")
                    try: driver.quit()
                    except Exception: pass
                    del self._driver_usage[d_id]
                    driver = self._create_driver()
                else:
                    try: driver.delete_all_cookies()
                    except Exception: pass

                self._available.append(driver)
                self._condition.notify()

    def shutdown(self) -> None:
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()

        for driver in list(self._in_use) + self._available:
            try: driver.quit()
            except Exception: pass

        self._available.clear()
        self._in_use.clear()
        self._driver_usage.clear()
        logger.info("Пул драйверов успешно очищен и остановлен")


_pool: Optional[DriverPool] = None

def init_pool(max_drivers: int = 3) -> DriverPool:
    global _pool
    if _pool is None:
        _pool = DriverPool(max_drivers=max_drivers)
    return _pool

def get_pool() -> DriverPool:
    if _pool is None:
        raise RuntimeError("Пул не инициализирован. Вызовите init_pool()")
    return _pool