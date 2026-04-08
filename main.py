import os
import logging

import dotenv
import telebot

from handlers.command_handlers import register_command_handlers
from handlers.callback_handlers import register_callback_handlers
from handlers.message_handlers import register_message_handlers


dotenv.load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN", "REPLACE_WITH_YOUR_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bot():
    bot = telebot.TeleBot(API_TOKEN)
    register_command_handlers(bot)
    register_callback_handlers(bot)
    register_message_handlers(bot)
    return bot


if __name__ == "__main__":
    if API_TOKEN == "REPLACE_WITH_YOUR_TOKEN":
        print("Please set TELEGRAM_TOKEN in the environment or .env before running the bot.")
    else:
        bot = create_bot()
        print("Starting Lost & Found bot (press Ctrl+C to stop)", bot.get_me().username)
        bot.infinity_polling()
