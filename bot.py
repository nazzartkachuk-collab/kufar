import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fetchers import get_fiat_rates, get_crypto_rates

logger = logging.getLogger(__name__)


def format_fiat(rates: dict) -> str:
    if not rates:
        return "⚠️ Не удалось получить курсы валют. Попробуйте позже."
    lines = ["💱 *Курсы валют (НБРБ):*"]
    for pair, value in rates.items():
        lines.append(f"• {pair}: *{value}*")
    return "\n".join(lines)


def format_crypto(rates: dict) -> str:
    if not rates:
        return "⚠️ Не удалось получить курсы криптовалют. Попробуйте позже."
    lines = ["🪙 *Курсы криптовалют (USD):*"]
    for symbol, value in rates.items():
        lines.append(f"• {symbol}: *{value}*")
    return "\n".join(lines)


async def send_fiat_notification(bot: Bot, chat_id: int):
    rates = await get_fiat_rates()
    text = format_fiat(rates)
    await bot.send_message(chat_id, text, parse_mode="Markdown")


async def send_crypto_notification(bot: Bot, chat_id: int):
    rates = await get_crypto_rates()
    text = format_crypto(rates)
    await bot.send_message(chat_id, text, parse_mode="Markdown")


def setup_scheduler(bot: Bot, chat_id: int) -> AsyncIOScheduler:
    """
    Каждые 12 часов (08:00 и 20:00 по Минску) — курсы валют.
    Каждый час — курсы крипты.
    """
    scheduler = AsyncIOScheduler(timezone="Europe/Minsk")

    scheduler.add_job(
        send_fiat_notification,
        "cron",
        hour="8,20",
        minute=0,
        args=[bot, chat_id],
        id="fiat_cron",
        replace_existing=True,
    )

    scheduler.add_job(
        send_crypto_notification,
        "cron",
        minute=0,
        args=[bot, chat_id],
        id="crypto_cron",
        replace_existing=True,
    )

    return scheduler


async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот для отслеживания курсов.\n\n"
        "Доступные команды:\n"
        "/value — курсы валют (USD, EUR, 100 RUB к BYN)\n"
        "/crypto — курсы криптовалют (BTC, ETH, SOL, GRAM)\n\n"
        "Также я автоматически отправляю:\n"
        "• курсы валют — в 08:00 и 20:00\n"
        "• курсы крипты — каждый час"
    )


async def cmd_value(message: Message):
    rates = await get_fiat_rates()
    await message.answer(format_fiat(rates), parse_mode="Markdown")


async def cmd_crypto(message: Message):
    rates = await get_crypto_rates()
    await message.answer(format_crypto(rates), parse_mode="Markdown")


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_value, Command("value"))
    dp.message.register(cmd_crypto, Command("crypto"))
