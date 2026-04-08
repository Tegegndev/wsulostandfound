import os

import telebot

from utils import build_pending_id, set_pending_post


def submit_post_for_review(bot, chat_id: int, kind: str, data: dict):
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

    admin_id = int(os.getenv("ADMIN_ID"))
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
