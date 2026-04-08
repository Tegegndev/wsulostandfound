import math

import telebot

from database import get_items
from helpers import format_post
from localization import get_text
from services.report_service import report_to_admin


PAGE_SIZE = 5


def send_list_page(bot, chat_id: int, page: int, lang: str):
    try:
        items = get_items()
        if not items:
            bot.send_message(chat_id, get_text("no_posts", lang))
            return

        total_pages = max(1, math.ceil(len(items) / PAGE_SIZE))
        page = max(1, min(page, total_pages))
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = items[start:end]

        for item in page_items:
            bot.send_message(chat_id, format_post(item, lang))

        markup = telebot.types.InlineKeyboardMarkup()
        buttons = []
        if page > 1:
            buttons.append(telebot.types.InlineKeyboardButton("Prev", callback_data=f"list_page_{page - 1}"))
        if page < total_pages:
            buttons.append(telebot.types.InlineKeyboardButton("Next", callback_data=f"list_page_{page + 1}"))
        if buttons:
            markup.row(*buttons)
            bot.send_message(chat_id, f"Page {page}/{total_pages}", reply_markup=markup)
    except Exception as e:
        report_to_admin(bot, "send_list_page", e)
        bot.send_message(chat_id, "An error occurred. Please try again later.")
