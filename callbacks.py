import os
import logging

import telebot

from localization import get_text
from database import update_user_language, add_item
from helpers import invalidate_user_lang_cache, format_post
from utils import pending_posts


logger = logging.getLogger(__name__)


def register_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def handle_language_selection(call: telebot.types.CallbackQuery):
        lang_code = call.data[5:]
        telegram_id = call.message.chat.id
        try:
            update_user_language(telegram_id, lang_code)
            invalidate_user_lang_cache(telegram_id)
            lang = lang_code
            bot.answer_callback_query(call.id, get_text("language_set", lang, language=get_text(lang_code, lang)))
            bot.edit_message_text(get_text("choose_language", lang), call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.error(f"Error updating language: {e}")
            bot.answer_callback_query(call.id, "Error setting language.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
    def handle_admin_action(call: telebot.types.CallbackQuery):
        action, pending_id = call.data.split("_", 1)
        if pending_id not in pending_posts:
            bot.answer_callback_query(call.id, "Post not found.")
            return

        post = pending_posts[pending_id]
        user_id = post["user_id"]

        if action == "approve":
            try:
                added_item = add_item(
                    item_name=post["title"],
                    description=post["description"],
                    user_telegram_id=user_id,
                    type=post["kind"],
                    status="active",
                )
                if added_item and added_item.data:
                    item_data = added_item.data[0]
                    channel_username = os.getenv("CHANNEL_USERNAME")
                    formatted_post = format_post(item_data, "en")
                    bot.send_message(channel_username, formatted_post)

                bot.send_message(user_id, "Your post has been approved and published!")
                bot.answer_callback_query(call.id, "Post approved.")
            except Exception as e:
                logger.error(f"Error adding item: {e}")
                bot.answer_callback_query(call.id, "Error approving post.")
        elif action == "reject":
            bot.send_message(user_id, "Your post has been rejected.")
            bot.answer_callback_query(call.id, "Post rejected.")

        del pending_posts[pending_id]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
