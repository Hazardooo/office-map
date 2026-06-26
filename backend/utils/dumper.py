import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Настраиваем Chrome в headless-режиме (как у вас в пуле)
CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless=new")
CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
CHROME_OPTIONS.add_argument("--window-size=1280,720")

# !!! УКАЖИТЕ IP ПРИНТЕРА, КОТОРЫЙ СТАВИТ 100% !!!
PRINTER_IP = "10.100.0.29"


def dump_printer_page(ip):
    driver = webdriver.Chrome(options=CHROME_OPTIONS)
    driver.set_page_load_timeout(15)

    url = f"https://{ip}"
    print(f"[*] Подключаемся к принтеру {url}...")

    try:
        driver.get(url)
    except Exception as e:
        print(f"[-] Ошибка HTTPS, пробуем по HTTP... ({e})")
        url = f"http://{ip}"
        driver.get(url)

    print("[*] Ждем 5 секунд для загрузки скриптов...")
    time.sleep(5)

    output = []
    output.append("=== ГЛАВНЫЙ ДОКУМЕНТ (TOP LEVEL) ===")
    output.append(f"Title: {driver.title}")
    output.append(driver.page_source)
    output.append("\n" + "="*50 + "\n")

    # Ищем все фреймы на странице
    frames = driver.find_elements(By.TAG_NAME, "frame")
    if not frames:
        frames = driver.find_elements(By.TAG_NAME, "iframe")

    print(f"[+] Найдено фреймов на верхнем уровне: {len(frames)}")

    # Перебираем фреймы верхнего уровня
    for idx, frame in enumerate(frames):
        frame_name = frame.get_attribute("name") or frame.get_attribute("id") or f"index_{idx}"
        print(f"[*] Переключаемся во фрейм: '{frame_name}'")

        try:
            driver.switch_to.frame(frame)
            output.append(f"=== СОДЕРЖИМОЕ ФРЕЙМА: {frame_name} ===")
            output.append(driver.page_source)
            output.append("\n" + "="*50 + "\n")

            # Проверяем, нет ли внутри этого фрейма еще и вложенных фреймов (глубокий уровень)
            sub_frames = driver.find_elements(By.TAG_NAME, "frame") or driver.find_elements(By.TAG_NAME, "iframe")
            if sub_frames:
                print(f"    [+] Внутри '{frame_name}' найдено еще sub-фреймов: {len(sub_frames)}")
                for s_idx, sub_frame in enumerate(sub_frames):
                    sub_name = sub_frame.get_attribute("name") or sub_frame.get_attribute("id") or f"sub_{s_idx}"
                    try:
                        driver.switch_to.frame(sub_frame)
                        output.append(f"=== ВЛОЖЕННЫЙ ФРЕЙМ: {frame_name} -> {sub_name} ===")
                        output.append(driver.page_source)
                        output.append("\n" + "="*50 + "\n")
                        driver.switch_to.parent_frame() # Возврат на уровень выше
                    except Exception as sub_e:
                        print(f"    [-] Не удалось зайти в sub-фрейм {sub_name}: {sub_e}")

            driver.switch_to.default_content() # Возврат на самый верх
        except Exception as e:
            print(f"[-] Не удалось зайти во фрейм {frame_name}: {e}")
            driver.switch_to.default_content()

    driver.quit()

    # Сохраняем весь лог в файл
    filename = "hp_page_structure4.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"\n[INFO] Структура страницы успешно записана в файл: {filename}")
    print("[INFO] Скопируйте содержимое этого файла или прикрепите его сюда.")

if __name__ == "__main__":
    dump_printer_page(PRINTER_IP)
