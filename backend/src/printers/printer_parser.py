from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    url = "https://10.100.0.34/wlmpor/index.htm"
    driver.get(url)

    # Ждём и переключаемся в основной фрейм
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "wlmframe"))
    )
    driver.switch_to.frame("wlmframe")

    # Ждём iframe тонера
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "toner"))
    )
    time.sleep(3)

    # Переключаемся в iframe тонера
    driver.switch_to.frame("toner")
    time.sleep(2)

    # Парсим HTML
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Ищем таблицу тонера
    toner_table = soup.find("table", id="contentrow")
    if toner_table:
        for tr in toner_table.find_all("tr"):
            tds = tr.find_all("td")
            row_data = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]

            # Ищем строку с цветом и процентом
            color = None
            percent = None
            for text in row_data:
                if text in ["Черный", "Голубой", "Пурпурный", "Желтый"]:
                    color = text
                if "%" in text:
                    percent = text

            if color and percent:
                print(f"{color}: {percent}")

finally:
    driver.quit()