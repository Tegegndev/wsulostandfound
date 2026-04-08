import os
import logging

import telebot

from localization import get_text
from database import update_user_language, add_item
from helpers import invalidate_user_lang_cache, format_channel_post, get_user_lang
from services.list_service import send_list_page
from services.report_service import report_to_admin
from utils import get_pending_post, remove_pending_post


logger = logging.getLogger(__name__)


def register_callback_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def handle_language_selection(call: telebot.types.CallbackQuery):
        try:
            lang_code = call.data[5:]
            telegram_id = call.message.chat.id
            update_user_language(telegram_id, lang_code)
            invalidate_user_lang_cache(telegram_id)
            lang = lang_code
            bot.answer_callback_query(call.id, get_text("language_set", lang, language=get_text(lang_code, lang)))
            bot.edit_message_text(get_text("choose_language", lang), call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.error(f"Error updating language: {e}")
            report_to_admin(bot, "handle_language_selection", e)
            bot.answer_callback_query(call.id, "Error setting language.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
    def handle_admin_action(call: telebot.types.CallbackQuery):
        try:
            action, pending_id = call.data.split("_", 1)
            post = get_pending_post(pending_id)
            if not post:
                bot.answer_callback_query(call.id, "Post not found.")
                return

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
                        if not channel_username:
                            report_to_admin(bot, "handle_admin_action.approve", "CHANNEL_USERNAME is not set")
                        else:
                            formatted_post = format_channel_post(item_data, "en")
                            markup = telebot.types.InlineKeyboardMarkup()
                            item_id = item_data.get("id")
                            url = None
                            if item_id is not None:
                                try:
                                    bot_username = bot.get_me().username
                                except Exception as e:
                                    report_to_admin(bot, "handle_admin_action.approve", e)
                                    bot_username = None
                                if bot_username:
                                    url = f"https://t.me/{bot_username}?start=contact_{item_id}"
                            if item_id is not None and url:
                                markup.add(
                                    telebot.types.InlineKeyboardButton(
                                        "Contact Owner",
                                        url=url,
                                    )
                                )
                            bot.send_message(channel_username, formatted_post, reply_markup=markup, parse_mode="HTML")

                    bot.send_message(user_id, "Your post has been approved and published!")
                    bot.answer_callback_query(call.id, "Post approved.")
                except Exception as e:
                    logger.error(f"Error adding item: {e}")
                    report_to_admin(bot, "handle_admin_action.approve", e)
                    bot.answer_callback_query(call.id, "Error approving post.")
            elif action == "reject":
                bot.send_message(user_id, "Your post has been rejected.")
                bot.answer_callback_query(call.id, "Post rejected.")

            remove_pending_post(pending_id)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception as e:
            logger.exception("handle_admin_action failed")
            report_to_admin(bot, "handle_admin_action", e)
            bot.answer_callback_query(call.id, "Error processing action.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("list_page_"))
    def handle_list_pagination(call: telebot.types.CallbackQuery):
        try:
            page_str = call.data.split("_", 2)[2]
            if not page_str.isdigit():
                bot.answer_callback_query(call.id, "Invalid page.")
                return
            page = int(page_str)
            chat_id = call.message.chat.id
            lang = get_user_lang(chat_id)
            send_list_page(bot, chat_id, page, lang)
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("handle_list_pagination failed")
            report_to_admin(bot, "handle_list_pagination", e)
            bot.answer_callback_query(call.id, "Error loading page.")
