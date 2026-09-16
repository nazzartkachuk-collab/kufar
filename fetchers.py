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
    params = {"periodicity": 0}  # 0 = ежедневные курсы
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

    # API возвращает список объектов; индексируем по Cur_Abbreviation
    by_code = {item["Cur_Abbreviation"]: item for item in data}

    result = {}

    # USD
    if "USD" in by_code:
        usd = by_code["USD"]
        result["USD/BYN"] = f'{usd["Cur_OfficialRate"]:.4f}'

    # EUR
    if "EUR" in by_code:
        eur = by_code["EUR"]
        result["EUR/BYN"] = f'{eur["Cur_OfficialRate"]:.4f}'

    # RUB (курс за 1 RUB → умножаем на 100)
    if "RUB" in by_code:
        rub = by_code["RUB"]
        result["100 RUB/BYN"] = f'{rub["Cur_OfficialRate"] * 100:.4f}'

    return result


# ---------- КРИПТОВАЛЮТЫ (CoinGecko) ----------
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

# ID монет в CoinGecko
CRYPTO_IDS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "gram-2": "GRAM",   # актуальный ID для Gram (может меняться)
}


async def get_crypto_rates() -> dict:
    """
    Возвращает курсы BTC, ETH, SOL, GRAM в USD через CoinGecko.
    Бесплатный публичный API, ключ не нужен.
    """
    params = {
        "ids": ",".join(CRYPTO_IDS.keys()),
        "vs_currencies": "usd",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                COINGECKO_URL, params=params, timeout=15
            ) as resp:
                if resp.status != 200:
                    logger.error("CoinGecko вернул статус %s", resp.status)
                    return {}
                data = await resp.json()
    except Exception as e:
        logger.exception("Ошибка запроса к CoinGecko: %s", e)
        return {}

    result = {}
    for cg_id, symbol in CRYPTO_IDS.items():
        if cg_id in data and "usd" in data[cg_id]:
            price = data[cg_id]["usd"]
            result[symbol] = f"${price:,.2f}"
        else:
            result[symbol] = "н/д"

    return result