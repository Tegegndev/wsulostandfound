import os

import telebot

from localization import get_text


def send_join_channel_prompt(bot, chat_id: int):
    channel_username = os.getenv("CHANNEL_USERNAME")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "Join Channel",
            url=f"https://t.me/{channel_username[1:]}",
        )
    )
    bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)


def build_main_menu_markup(lang: str):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(get_text("list", lang), get_text("search", lang))
    markup.row(get_text("post_lost", lang), get_text("post_found", lang))
    markup.row(get_text("settings", lang), get_text("help", lang))
    return markup


def send_main_menu(bot, chat_id: int, lang: str):
    bot.send_message(chat_id, get_text("welcome", lang), reply_markup=build_main_menu_markup(lang))
