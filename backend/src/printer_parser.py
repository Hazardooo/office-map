
import asyncio
import json
import logging
import random
import re
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("printer_parser")


# --- MOCK / SIMULATION FOR TESTING ---
def get_mock_printer_data(ip: str) -> Dict[str, Any]:
    """Генерирует реалистичные тестовые данные для демо-принтеров"""
    seed_sum = (
        sum(int(char) for char in ip if char.isdigit())
        if any(char.isdigit() for char in ip)
        else 42
    )

    rng = random.Random(seed_sum)

    status_options = ["online", "online", "online", "low_toner", "no_paper"]
    status = rng.choice(status_options)

    if "color" in ip.lower() or seed_sum % 3 == 0:
        t_cyan = rng.randint(5, 100)
        t_magenta = rng.randint(5, 100)
        t_yellow = rng.randint(5, 100)
        t_black = rng.randint(2, 100)

        if any(t < 10 for t in [t_cyan, t_magenta, t_yellow, t_black]):
            status = "low_toner"

        return {
            "status": status,
            "toner_black": t_black,
            "toner_cyan": t_cyan,
            "toner_magenta": t_magenta,
            "toner_yellow": t_yellow,
            "model": (
                "HP Color LaserJet Pro MFP (Demo)"
                if seed_sum % 2 == 0
                else "Kyocera ECOSYS Color (Demo)"
            ),
        }
    else:
        t_black = rng.randint(2, 100)
        if t_black < 10:
            status = "low_toner"

        return {
            "status": status,
            "toner_black": t_black,
            "toner_cyan": None,
            "toner_magenta": None,
            "toner_yellow": None,
            "model": (
                "Kyocera ECOSYS M2040dn (Demo)"
                if seed_sum % 2 == 0
                else "HP LaserJet Pro M402dn (Demo)"
            ),
        }


# --- HTTP HELPER ---


async def safe_get(
    client: httpx.AsyncClient, url: str, retries: int = 1, **kwargs
) -> Optional[httpx.Response]:
    """
    Делает GET-запрос с retry на disconnect.
    Kyocera часто рвёт keep-alive соединения — ловим RemoteProtocolError.
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = await client.get(url, **kwargs)
            return response
        except (httpx.RemoteProtocolError, httpx.ServerDisconnected) as e:
            last_error = e
            logger.debug(f"[{url}] Disconnect on attempt {attempt + 1}: {e}")
            if attempt < retries:
                await asyncio.sleep(0.3)
                continue
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
            raise  # Эти не ретраим — принтер реально оффлайн
    raise last_error  # type: ignore


# --- REAL PRINTER PARSERS ---


async def parse_hp_printer(
    client: httpx.AsyncClient, base_url: str
) -> Optional[Dict[str, Any]]:
    """Парсинг XML/HTML интерфейса HP JetDirect / HP Web Jetadmin"""
    try:
        response = await safe_get(
            client,
            f"{base_url}/DevMgmt/ProductStatusDyn.xml",
            timeout=2.0,
            headers={"Connection": "close"},
        )
        if response.status_code == 200:
            xml_text = response.text
            black_match = re.search(
                r"<dd:ConsumablePercentageLevelRemaining[^>]*>(\d+)</dd:ConsumablePercentageLevelRemaining>",
                xml_text,
            )
            if not black_match:
                black_match = re.search(
                    r"<ConsumablePercentageLevelRemaining[^>]*>(\d+)</ConsumablePercentageLevelRemaining>",
                    xml_text,
                )

            if black_match:
                black_toner = int(black_match.group(1))
                return {
                    "status": "online" if black_toner > 10 else "low_toner",
                    "toner_black": black_toner,
                    "toner_cyan": None,
                    "toner_magenta": None,
                    "toner_yellow": None,
                    "model": "HP LaserJet",
                }
    except Exception as e:
        logger.debug(f"HP XML parsing failed for {base_url}: {e}")

    try:
        response = await safe_get(
            client,
            f"{base_url}/index.htm",
            timeout=2.0,
            headers={"Connection": "close"},
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            text_content = soup.get_text()
            percent_matches = re.findall(r"(\d+)%", text_content)
            if percent_matches:
                return {
                    "status": "online",
                    "toner_black": int(percent_matches[0]),
                    "toner_cyan": None,
                    "toner_magenta": None,
                    "toner_yellow": None,
                }
    except Exception:
        pass

    return None


async def parse_kyocera_printer(
    client: httpx.AsyncClient, base_url: str
) -> Optional[Dict[str, Any]]:
    """
    Парсинг Kyocera Command Center RX.
    Сначала пытается извлечь данные из inline JS (Hme_TonerModel),
    затем fallback на эвристический парсинг HTML.
    """
    # Порядок: сначала те, что точнее, потом fallback
    urls_to_try = [
        f"{base_url}/startw_device.htm",
        f"{base_url}/",
        f"{base_url}/index.htm",
        f"{base_url}/startwlm/device.htm",
        f"{base_url}/device.htm",
        f"{base_url}/status.htm",
        f"{base_url}/home.htm",
    ]

    html = None
    used_url = None

    for url in urls_to_try:
        try:
            response = await safe_get(
                client,
                url,
                retries=1,
                timeout=5.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;"
                        "q=0.9,image/webp,*/*;q=0.8"
                    ),
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "identity",  # <-- Kyocera ломается на gzip
                    "Connection": "close",  # <-- НЕ держим соединение
                },
            )
            if response.status_code in (200, 301, 302, 303, 307, 308):
                html = response.text
                used_url = url
                logger.debug(f"Kyocera ответил на {url}: {response.status_code}")
                break
        except (httpx.RemoteProtocolError, httpx.ServerDisconnected) as e:
            logger.debug(f"Kyocera disconnect on {url}: {e}")
            continue
        except Exception as e:
            logger.debug(f"Kyocera request failed for {url}: {e}")
            continue

    if not html:
        return None

    # ─── Способ 1: Вытащить массив Renaming из inline JS ───
    renaming_match = re.search(
        r'Hme_TonerModel\.(?:set|put)\(\s*["' ']Renaming["' "]\s*,\s*(\[[^\]]*\])",
        html,
        re.IGNORECASE,
    )
    color_match = re.search(
        r'Hme_TonerModel\.(?:set|put)\(\s*["'
        ']ColorOrMono["'
        ']\s*,\s*["'
        ']([^"'
        ']+)["'
        "]",
        html,
        re.IGNORECASE,
    )

    if renaming_match:
        try:
            json_str = renaming_match.group(1).replace("'", '"')
            renaming = json.loads(json_str)

            levels = []
            for val in renaming:
                clean = val.replace("&nbsp;", "").strip()
                if clean and clean not in ("", "-1"):
                    levels.append(int(clean))
                else:
                    levels.append(None)

            is_color = (
                color_match.group(1).lower() == "color"
                if color_match
                else len(levels) > 1
            )

            result: Dict[str, Any] = {
                "model": "Kyocera ECOSYS",
                "toner_black": levels[0] if len(levels) > 0 else None,
                "toner_cyan": levels[1] if len(levels) > 1 and is_color else None,
                "toner_magenta": levels[2] if len(levels) > 2 and is_color else None,
                "toner_yellow": levels[3] if len(levels) > 3 and is_color else None,
            }

            all_levels = [
                v
                for v in [
                    result["toner_black"],
                    result["toner_cyan"],
                    result["toner_magenta"],
                    result["toner_yellow"],
                ]
                if v is not None
            ]
            result["status"] = (
                "low_toner"
                if any(v is not None and v < 10 for v in all_levels)
                else "online"
            )
            logger.info(f"Kyocera JS-модель распарсена с {used_url}: {result}")
            return result

        except Exception as e:
            logger.debug(f"Kyocera JS model parsing failed: {e}")

    # ─── Способ 2: Fallback на эвристический парсинг HTML ───
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    color_patterns = {
        "toner_black": [
            r"Черн(?:ый|ого)[^\d]{0,30}?(\d+)%",
            r"Black[^\d]{0,30}?(\d+)%",
            r"Картридж[^\d]{0,30}?Черн[^\d]{0,20}?(\d+)%",
        ],
        "toner_cyan": [
            r"Голуб(?:ой|ого)[^\d]{0,30}?(\d+)%",
            r"Cyan[^\d]{0,30}?(\d+)%",
        ],
        "toner_magenta": [
            r"Пурпурн(?:ый|ого)[^\d]{0,30}?(\d+)%",
            r"Magenta[^\d]{0,30}?(\d+)%",
        ],
        "toner_yellow": [
            r"Желт(?:ый|ого)[^\d]{0,30}?(\d+)%",
            r"Yellow[^\d]{0,30}?(\d+)%",
        ],
    }

    result: Dict[str, Any] = {"model": "Kyocera ECOSYS"}
    found_any = False

    for key, patterns in color_patterns.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                result[key] = int(m.group(1))
                found_any = True
                break
        else:
            result[key] = None

    is_color = any(
        result.get(k) is not None
        for k in ["toner_cyan", "toner_magenta", "toner_yellow"]
    )
    if not is_color:
        result["toner_cyan"] = result["toner_magenta"] = result["toner_yellow"] = None

    # Fallback: ищем процент рядом со словом "тонер"
    if result.get("toner_black") is None:
        toner_match = re.search(
            r"(?:тонер|toner|картридж|cartridge)[^\d]{0,50}?(\d+)%", text, re.IGNORECASE
        )
        if toner_match:
            result["toner_black"] = int(toner_match.group(1))
            found_any = True
        else:
            # Последний fallback — первый подходящий процент
            all_percents = re.findall(r"(\d+)%", text)
            for p in all_percents:
                idx = text.find(f"{p}%")
                context = text[max(0, idx - 30) : idx + 30]
                if not re.search(
                    r"бумаг|paper|кассет|cassette|лоток|tray", context, re.I
                ):
                    result["toner_black"] = int(p)
                    found_any = True
                    break

    if found_any:
        all_levels = [
            v
            for v in [
                result.get("toner_black"),
                result.get("toner_cyan"),
                result.get("toner_magenta"),
                result.get("toner_yellow"),
            ]
            if v is not None
        ]
        result["status"] = "low_toner" if any(v < 10 for v in all_levels) else "online"
        logger.info(f"Kyocera HTML fallback распарсен с {used_url}: {result}")
        return result

    return None


async def parse_generic_printer(
    client: httpx.AsyncClient, base_url: str
) -> Dict[str, Any]:
    """Универсальный эвристический парсер для любых принтеров по HTML содержимому"""
    response = await safe_get(
        client,
        base_url,
        retries=1,
        timeout=5.0,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    if response.status_code != 200:
        raise httpx.HTTPStatusError(
            "Не удалось открыть главную страницу принтера",
            request=response.request,
            response=response,
        )

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    black_toner = 100
    cyan_toner = None
    magenta_toner = None
    yellow_toner = None

    patterns = [
        r"(?:black|черный|k|toner|картридж)[\s\S]{0,30}?(\d+)\s*%",
        r"(\d+)\s*%\s*(?:black|черный|k|toner|картридж)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            black_toner = int(matches[0])
            break
    else:
        all_percents = re.findall(r"(\d+)\s*%", text)
        for p in all_percents:
            idx = text.find(f"{p}%")
            context = text[max(0, idx - 30) : idx + 30]
            if not re.search(r"бумаг|paper|кассет|cassette|лоток|tray", context, re.I):
                black_toner = int(p)
                break

    cyan_match = re.search(
        r"(?:cyan|голубой|c)[\s\S]{0,30}?(\d+)\s*%", text, re.IGNORECASE
    )
    if cyan_match:
        cyan_toner = int(cyan_match.group(1))

    magenta_match = re.search(
        r"(?:magenta|пурпурный|m)[\s\S]{0,30}?(\d+)\s*%", text, re.IGNORECASE
    )
    if magenta_match:
        magenta_toner = int(magenta_match.group(1))

    yellow_match = re.search(
        r"(?:yellow|желтый|y)[\s\S]{0,30}?(\d+)\s*%", text, re.IGNORECASE
    )
    if yellow_match:
        yellow_toner = int(yellow_match.group(1))

    model = "Network Printer"
    if soup.title and soup.title.string:
        title_str = soup.title.string.strip()
        if (
            len(title_str) > 3
            and "home" not in title_str.lower()
            and "status" not in title_str.lower()
        ):
            model = title_str

    status = "online"
    if black_toner < 10 or (
        cyan_toner is not None
        and any(t < 10 for t in [cyan_toner, magenta_toner, yellow_toner, black_toner])
    ):
        status = "low_toner"

    return {
        "status": status,
        "toner_black": black_toner,
        "toner_cyan": cyan_toner,
        "toner_magenta": magenta_toner,
        "toner_yellow": yellow_toner,
        "model": model,
    }


# --- MAIN API FUNCTION ---


async def fetch_printer_data(ip: str) -> Dict[str, Any]:
    """
    Основная функция опроса принтера по IP.
    Если IP содержит слово 'demo', 'test' или является локальным адресом 127.0.0.x,
    то возвращает симулированные данные.
    """
    clean_ip = ip.strip()

    if (
        "demo" in clean_ip.lower()
        or "test" in clean_ip.lower()
        or clean_ip.startswith("127.")
        or clean_ip.lower() == "localhost"
    ):
        return get_mock_printer_data(clean_ip)

    base_url = f"http://{clean_ip}"

    # Отключаем keep-alive полностью — принтеры не умеют в persistent connections
    limits = httpx.Limits(max_keepalive_connections=0, max_connections=1)

    async with httpx.AsyncClient(
        verify=False,
        timeout=5.0,
        limits=limits,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    ) as client:
        try:
            # СНАЧАЛА Kyocera — у пользователя Kyocera, не тратим соединение на HP
            kyocera_data = await parse_kyocera_printer(client, base_url)
            if kyocera_data:
                return kyocera_data

            # Потом HP
            hp_data = await parse_hp_printer(client, base_url)
            if hp_data:
                return hp_data

            # Универсальный парсер
            generic_data = await parse_generic_printer(client, base_url)
            return generic_data

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            logger.warning(f"Принтер по IP {clean_ip} не отвечает (Offline): {e}")
            return {
                "status": "offline",
                "toner_black": 0,
                "toner_cyan": None,
                "toner_magenta": None,
                "toner_yellow": None,
            }
        except (httpx.RemoteProtocolError, httpx.ServerDisconnected) as e:
            logger.warning(
                f"Принтер по IP {clean_ip} разорвал соединение (возможно, требует HTTPS): {e}"
            )
            return {
                "status": "offline",
                "toner_black": 0,
                "toner_cyan": None,
                "toner_magenta": None,
                "toner_yellow": None,
            }
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при опросе принтера {clean_ip}: {e}")
            return {
                "status": "offline",
                "toner_black": 0,
                "toner_cyan": None,
                "toner_magenta": None,
                "toner_yellow": None,
            }
