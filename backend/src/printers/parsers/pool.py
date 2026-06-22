import threading
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

# Оптимизированные опции Chrome
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
CHROME_OPTIONS.add_argument("--disable-javascript")  # Осторожно: если сайт без JS работает
CHROME_OPTIONS.add_argument("--blink-settings=imagesEnabled=false")
CHROME_OPTIONS.add_argument("--window-size=1280,720")
CHROME_OPTIONS.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.default_content_setting_values.notifications": 2,
})

# Отключаем логи Chrome
CHROME_OPTIONS.add_experimental_option("excludeSwitches", ["enable-logging"])


class DriverPool:
    """Пул переиспользуемых Chrome-драйверов."""

    def __init__(self, max_drivers: int = 3):
        self._max = max_drivers
        self._available: list[webdriver.Chrome] = []
        self._in_use: set[webdriver.Chrome] = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._shutdown = False

        # Предзагружаем драйверы
        for _ in range(max_drivers):
            try:
                driver = self._create_driver()
                self._available.append(driver)
                logger.info(f"Драйвер #{len(self._available)} создан")
            except Exception as e:
                logger.error(f"Не удалось создать драйвер: {e}")

    def _create_driver(self) -> webdriver.Chrome:
        service = Service(log_path="/dev/null")  # отключаем логи chromedriver
        return webdriver.Chrome(options=CHROME_OPTIONS, service=service)

    def acquire(self, timeout: float = 30.0) -> Optional[webdriver.Chrome]:
        with self._condition:
            if self._shutdown:
                return None

            deadline = threading.current_thread().ident + timeout  # упрощённо

            while not self._available and not self._shutdown:
                if not self._condition.wait(timeout=timeout):
                    logger.warning("Таймаут ожидания драйвера из пула")
                    return None

            if self._available:
                driver = self._available.pop()
                self._in_use.add(driver)
                return driver

            return None

    def release(self, driver: webdriver.Chrome) -> None:
        with self._condition:
            if driver in self._in_use:
                self._in_use.remove(driver)
                # Очищаем cookies и localStorage для чистоты
                try:
                    driver.delete_all_cookies()
                except Exception:
                    pass
                self._available.append(driver)
                self._condition.notify()

    def shutdown(self) -> None:
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()

        for driver in list(self._in_use):
            try:
                driver.quit()
            except Exception:
                pass

        for driver in self._available:
            try:
                driver.quit()
            except Exception:
                pass

        self._available.clear()
        self._in_use.clear()
        logger.info("Пул драйверов остановлен")


# Глобальный пул
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


def shutdown_pool() -> None:
    global _pool
    if _pool:
        _pool.shutdown()
        _pool = None