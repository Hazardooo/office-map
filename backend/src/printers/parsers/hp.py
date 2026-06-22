# parsers/hp.py
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict

from .base import BasePrinterParser


class HPParser(BasePrinterParser):
    """Универсальный парсер для HP LaserJet (все модели)."""

    COLOR_MAP = {
        "черн": "Черный",
        "black": "Черный",
        "голуб": "Голубой",
        "cyan": "Голубой",
        "пурпур": "Пурпурный",
        "magenta": "Пурпурный",
        "желт": "Желтый",
        "yellow": "Желтый",
    }

    BG_COLOR_MAP = {
        "#000000": "Черный",
        "#00ffff": "Голубой",
        "#ff00ff": "Пурпурный",
        "#ffff00": "Желтый",
    }

    def _detect_color(self, text: str) -> str | None:
        text_lower = text.lower()
        for key, color in self.COLOR_MAP.items():
            if key in text_lower:
                return color
        return None

    def _extract_percent(self, text: str) -> str | None:
        # Ищем число+%, возможно с * или другими символами
        match = re.search(r'(\d+)%', text)
        if match:
            return f"{match.group(1)}%"
        return None

    def _extract_percent_from_width(self, style: str) -> str | None:
        match = re.search(r'WIDTH:\s*(\d+)%', style, re.IGNORECASE)
        if match:
            return f"{match.group(1)}%"
        return None

    def _parse_supply_block(self, block) -> tuple[str | None, str | None]:
        """
        Парсит один блок расходного материала.
        Возвращает (color, percent) или (None, None)
        """
        color = None
        percent = None

        # 1. Ищем цвет в тексте блока
        block_text = block.get_text(separator=' ', strip=True)
        color = self._detect_color(block_text)

        # 2. Ищем процент в тексте (включая nowrap td)
        for td in block.find_all("td"):
            text = td.get_text(strip=True)
            p = self._extract_percent(text)
            if p:
                percent = p
                # Если цвет ещё не найден — пробуем определить из этого td
                if not color:
                    color = self._detect_color(text)
                break

        # 3. Если процент не найден в тексте — ищем в WIDTH style
        if not percent:
            for td in block.find_all("td", style=re.compile(r'WIDTH')):
                style = td.get("style", "")
                # Проверяем, что это цветная полоса (не белая #FFFFFF)
                bg_match = re.search(r'BACKGROUND-COLOR:\s*([#A-Fa-f0-9]+)', style, re.IGNORECASE)
                if bg_match:
                    bg = bg_match.group(1).lower()
                    if bg != "#ffffff" and bg != "#eeeeee":
                        # Определяем цвет по background, если ещё не найден
                        if not color:
                            color = self.BG_COLOR_MAP.get(bg)
                        p = self._extract_percent_from_width(style)
                        if p and p != "0%":
                            percent = p
                            break

        return color, percent

    def get_toner(self) -> Dict[str, str]:
        try:
            url = f"http://{self.ip}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            result = {}

            # Стратегия 1: Ищем таблицы mainContentArea
            tables = soup.find_all("table", class_="mainContentArea")
            if not tables:
                tables = soup.find_all("table", class_=re.compile(r'mainContentArea'))

            for table in tables:
                # Вариант A: Ячейки с width25/width20/width30 (M276nw, M176n)
                for td in table.find_all("td", width=re.compile(r'25%|20%|30%')):
                    color, percent = self._parse_supply_block(td)
                    if color and percent:
                        result[color] = percent

                # Вариант B: Строки с tableDataCellStand (P2055dn)
                for tr in table.find_all("tr"):
                    tds = tr.find_all("td", class_=re.compile(r'tableDataCellStand|tableDataCell'))
                    if len(tds) >= 2:
                        color = self._detect_color(tds[0].get_text(strip=True))
                        percent = None

                        # Ищем процент во вложенных td с WIDTH
                        for nested_td in tr.find_all("td", style=re.compile(r'WIDTH')):
                            style = nested_td.get("style", "")
                            bg_match = re.search(r'BACKGROUND-COLOR:\s*([#A-Fa-f0-9]+)', style, re.IGNORECASE)
                            if bg_match and bg_match.group(1).lower() not in ("#ffffff", "#eeeeee"):
                                p = self._extract_percent_from_width(style)
                                if p and p != "0%":
                                    percent = p
                                    break

                        # Или ищем процент в тексте ячеек
                        if not percent:
                            for td in tds:
                                p = self._extract_percent(td.get_text(strip=True))
                                if p:
                                    percent = p
                                    break

                        if color and percent:
                            result[color] = percent

            # Стратегия 2: Fallback — ищем hpGasGaugeBorder по всей странице
            if not result:
                for gauge_table in soup.find_all("table", class_="hpGasGaugeBorder"):
                    # Ищем родительский td, чтобы определить контекст
                    parent_td = gauge_table.find_parent("td")
                    if parent_td:
                        color, percent = self._parse_supply_block(parent_td)
                        if color and percent:
                            result[color] = percent

            # Стратегия 3: Ещё fallback — по background-color напрямую
            if not result:
                for td in soup.find_all("td", style=re.compile(r'BACKGROUND-COLOR')):
                    style = td.get("style", "")
                    bg_match = re.search(r'BACKGROUND-COLOR:\s*([#A-Fa-f0-9]+)', style, re.IGNORECASE)
                    if bg_match:
                        bg = bg_match.group(1).lower()
                        if bg in self.BG_COLOR_MAP:
                            color = self.BG_COLOR_MAP[bg]
                            p = self._extract_percent_from_width(style)
                            if p and p not in ("0%", "100%"):
                                # Проверяем, что это не пустая полоса
                                result[color] = p

            # Фильтруем дубликаты и барабаны
            filtered = {}
            for color, percent in result.items():
                if color and percent and color != "Барабан":
                    filtered[color] = percent

            return filtered if filtered else {"error": "Данные о тонере не найдены"}

        except requests.RequestException as e:
            return {"error": f"Ошибка запроса: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    def get_status(self) -> Dict[str, str]:
        try:
            url = f"http://{self.ip}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Модель из title
            model = "Unknown"
            title = soup.find("title")
            if title:
                title_text = title.get_text(strip=True)
                # Убираем IP: "HP LaserJet Pro MFP M176n   10.100.1.118"
                parts = re.split(r'&nbsp;|\s{2,}', title_text)
                model = parts[0].strip() if parts else title_text

            # Hostname из userId
            hostname = "Unknown"
            user_id_div = soup.find("div", class_="userId")
            if user_id_div:
                text = user_id_div.get_text(strip=True)
                # Ищем NPIxxx, CNxxx, DEVxxx
                hw_match = re.search(r'(NPI[A-Fa-f0-9]+|CN[A-Fa-f0-9]+|DEV[A-Fa-f0-9]+)', text, re.IGNORECASE)
                if hw_match:
                    hostname = hw_match.group(1).upper()

            # Статус
            status = "Unknown"
            status_cell = soup.find("td", id="deviceStatus_tableCell")
            if status_cell:
                status = status_cell.get_text(strip=True)
            else:
                # Ищем по labelLargeFont
                for td in soup.find_all("td", class_="labelLargeFont"):
                    if "Состояние" in td.get_text():
                        next_td = td.find_next_sibling("td")
                        if next_td:
                            status = next_td.get_text(strip=True)
                            break

            toner = self.get_toner()
            if "error" in toner:
                return toner

            return {
                "model": model,
                "hostname": hostname,
                "status": status,
                "toner": toner
            }

        except Exception as e:
            return {"error": str(e)}