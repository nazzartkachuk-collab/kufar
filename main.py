import asyncio
import logging
import os
import threading

from flask import Flask

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot import register_handlers, setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------- Flask для keep-alive ----------
app = Flask(__name__)


@app.route("/")
@app.route("/health")
def health():
    return "OK", 200


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ---------- Telegram-бот ----------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
# ID чата, куда бот шлёт уведомления. Узнайте свой ID через @userinfobot.
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))


async def main():
       bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    register_handlers(dp)

    # Планировщик
    scheduler = setup_scheduler(bot, ADMIN_CHAT_ID)
    scheduler.start()
    logger.info("Планировщик запущен")

    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    # Бот в основном потоке
    asyncio.run(main())
