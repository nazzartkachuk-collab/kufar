import aiohttp
import logging

logger = logging.getLogger(__name__)


# ---------- ВАЛЮТЫ (Нацбанк Беларуси) ----------
NBRB_URL = "https://api.nbrb.by/exrates/rates"


async def get_fiat_rates() -> dict:
    """
    Возвращает курсы USD/BYN, EUR/BYN и 100 RUB/BYN.
    API НБРБ: https://api.nbrb.by/exrates/rates?periodicity=0
    """
    params = {"periodicity": 0}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(NBRB_URL, params=params, timeout=15) as resp:
                if resp.status != 200:
                    logger.error("НБРБ вернул статус %s", resp.status)
                    return {}
                data = await resp.json()
    except Exception as e:
        logger.exception("Ошибка запроса к НБРБ: %s", e)
        return {}

    by_code = {item["Cur_Abbreviation"]: item for item in data}
    result = {}

    if "USD" in by_code:
        result["USD/BYN"] = f'{by_code["USD"]["Cur_OfficialRate"]:.4f}'
    if "EUR" in by_code:
        result["EUR/BYN"] = f'{by_code["EUR"]["Cur_OfficialRate"]:.4f}'
    if "RUB" in by_code:
        result["100 RUB/BYN"] = f'{by_code["RUB"]["Cur_OfficialRate"] * 100:.4f}'

    return result


# ---------- КРИПТОВАЛЮТЫ (Binance) ----------
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

SYMBOL_NAMES = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH",
    "SOLUSDT": "SOL",
}


async def get_crypto_rates() -> dict:
    """
    Возвращает курсы BTC, ETH, SOL в USDT через публичный API Binance.
    Не требует API-ключа. Лимиты для базовых запросов отсутствуют.
    """
    symbols_param = '["' + '","'.join(SYMBOLS) + '"]'
    params = {"symbols": symbols_param}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BINANCE_URL, params=params, timeout=15
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        "Binance вернул статус %s: %s", resp.status, body[:200]
                    )
                    return {}
                data = await resp.json()
    except Exception as e:
        logger.exception("Ошибка запроса к Binance: %s", e)
        return {}

    result = {}
    for item in data:
        symbol = item.get("symbol")
        price = item.get("price")
        if symbol in SYMBOL_NAMES and price is not None:
            result[SYMBOL_NAMES[symbol]] = f"${float(price):,.2f}"

    return result
