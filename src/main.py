# src/main.py
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from .config import BOT_TOKEN
from .handlers import start, on_ready, make_move

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_ready, pattern=r"^ready_"))
    app.add_handler(CallbackQueryHandler(make_move, pattern=r"^move_"))

    logger.info("Bot started!")
    app.run_polling()


if __name__ == "__main__":
    main()
