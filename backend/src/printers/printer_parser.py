import requests
from bs4 import BeautifulSoup

# 1. URL страницы, которую хотим запарсить
url = "http://10.100.0.16"  # Отличный тестовый сайт с цитатами

# 2. Добавляем User-Agent, чтобы сайт думал, что мы обычный браузер
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 3. Скачиваем страницу
response = requests.get(url, headers=headers)

# Проверяем, что запрос прошел успешно (код 200)
if response.status_code == 200:
    # 4. Передаем HTML-код в BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # 5. Ищем нужные элементы на странице
    # Например, найдем все блоки с цитатами (на этом сайте они в тегах <span class="text">)
    quotes = soup.find_all("span", class_="text")

    # 6. Выводим текст каждой цитаты
    for index, quote in enumerate(quotes, 1):
        print(f"{index}. {quote.text}")
else:
    print(f"Ошибка при загрузке страницы: {response.status_code}")