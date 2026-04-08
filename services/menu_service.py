import os

import telebot

from localization import get_text
from helpers import get_dual_text
from services.report_service import report_to_admin


def send_join_channel_prompt(bot, chat_id: int):
    try:
        channel_username = os.getenv("CHANNEL_USERNAME")
        if not channel_username:
            bot.send_message(chat_id, "Channel is not configured. Please contact admin.")
            return

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Join Channel",
                url=f"https://t.me/{channel_username[1:]}",
            )
        )
        bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
    except Exception as e:
        report_to_admin(bot, "send_join_channel_prompt", e)
        bot.send_message(chat_id, "An error occurred. Please try again later.")


def build_main_menu_markup(lang: str):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(get_text("list", lang), get_text("search", lang))
    markup.row(get_text("post_lost", lang), get_text("post_found", lang))
    markup.row(get_text("settings", lang), get_text("help", lang))
    return markup


def send_main_menu(bot, chat_id: int, lang: str, dual: bool = False):
    try:
        welcome_text = get_dual_text("welcome") if dual else get_text("welcome", lang)
        bot.send_message(chat_id, welcome_text, reply_markup=build_main_menu_markup(lang))
    except Exception as e:
        report_to_admin(bot, "send_main_menu", e)
        bot.send_message(chat_id, "An error occurred. Please try again later.")
