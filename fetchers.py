import aiohttp
import logging

logger = logging.getLogger(__name__)

# ---------- КРИПТОВАЛЮТЫ (Binance) ----------
# Публичный API Binance. Ключ не требуется.
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"

# Список монет. GRAM на Binance не торгуется, поэтому его не будет.
# Если нужен GRAM, см. Способ 2 в ответе.
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Красивые названия для вывода в сообщении
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
    # Формируем строку с символами, как требует Binance:
    # ["BTCUSDT","ETHUSDT","SOLUSDT"]
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
    # data — это список словарей: [{"symbol": "BTCUSDT", "price": "..."}, ...]
    for item in data:
        symbol = item.get("symbol")
        price = item.get("price")
        if symbol in SYMBOL_NAMES and price is not None:
            pretty_name = SYMBOL_NAMES[symbol]
            # Binance отдаёт цену строкой, преобразуем в float и форматируем
            result[pretty_name] = f"${float(price):,.2f}"

    return result
