import os

import telebot

from utils import build_pending_id, set_pending_post
from services.report_service import report_to_admin


def submit_post_for_review(bot, chat_id: int, kind: str, data: dict):
    try:
        pending_id = build_pending_id(chat_id)
        set_pending_post(
            pending_id,
            {
                "kind": kind,
                "title": data["title"],
                "description": data["description"],
                "contact": data["contact"],
                "user_id": chat_id,
            },
        )

        admin_id_raw = os.getenv("ADMIN_ID")
        if not admin_id_raw:
            bot.send_message(chat_id, "Admin is not configured. Please try again later.")
            return

        admin_id = int(admin_id_raw)
        formatted = (
            f"New {kind} Item:\n"
            f"Title: {data['title']}\n"
            f"Description: {data['description']}\n"
            f"Contact: {data['contact']}\n"
            f"User ID: {chat_id}"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("Approve", callback_data=f"approve_{pending_id}"),
            telebot.types.InlineKeyboardButton("Reject", callback_data=f"reject_{pending_id}"),
        )
        bot.send_message(admin_id, formatted, reply_markup=markup)
        bot.send_message(chat_id, "Your post has been submitted for review.")
    except Exception as e:
        report_to_admin(bot, "submit_post_for_review", e)
        bot.send_message(chat_id, "An error occurred. Please try again later.")
