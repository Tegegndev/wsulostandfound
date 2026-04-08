import logging

import telebot

from database import create_user, get_items, search_items
from helpers import ensure_user_registered, get_user_lang, is_user_member, format_post, start_post_flow
from localization import get_text, get_supported_languages
from services.menu_service import send_join_channel_prompt, send_main_menu
from services.post_service import submit_post_for_review
from utils import get_user_state, set_user_state, clear_user_state, has_user_state


logger = logging.getLogger(__name__)
MENU_KEYS = ("list", "search", "post_lost", "post_found", "settings", "help")


def _build_menu_button_texts() -> set[str]:
    texts = set()
    for lang_code in get_supported_languages():
        for key in MENU_KEYS:
            texts.add(get_text(key, lang_code))
    return texts


def register_message_handlers(bot):
    menu_button_texts = _build_menu_button_texts()

    @bot.message_handler(func=lambda m: bool(m.text and m.text.strip() in menu_button_texts))
    def handle_button_press(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return

        lang = get_user_lang(chat_id)
        menu_actions = {
            get_text("list", lang): "list",
            get_text("search", lang): "search",
            get_text("post_lost", lang): "post_lost",
            get_text("post_found", lang): "post_found",
            get_text("settings", lang): "settings",
            get_text("help", lang): "help",
        }

        action = menu_actions.get(message.text.strip())
        ensure_user_registered(chat_id, message)

        if action == "list":
            posts = get_items()
            if not posts:
                bot.reply_to(message, get_text("no_posts", lang))
                return
            for post in posts:
                bot.send_message(chat_id, format_post(post, lang))
            return

        if action == "search":
            set_user_state(chat_id, {"kind": "search", "step": "keyword"})
            bot.send_message(chat_id, get_text("search_prompt", lang))
            return

        if action == "post_lost":
            start_post_flow(message, "lost", bot)
            return

        if action == "post_found":
            start_post_flow(message, "found", bot)
            return

        if action == "settings":
            _show_settings(bot, message)
            return

        if action == "help":
            send_main_menu(bot, chat_id, lang)

    @bot.message_handler(content_types=["contact"])
    def handle_contact(message: telebot.types.Contact):
        chat_id = message.chat.id
        state = get_user_state(chat_id)
        if not state:
            return

        if state.get("kind") == "registration" and state.get("step") == "phone":
            phone = message.contact.phone_number
            username = message.from_user.username
            first_name = message.from_user.first_name
            try:
                create_user(chat_id, username, first_name, phone)
                bot.send_message(chat_id, get_text("registration_complete", "en"))
                send_main_menu(bot, chat_id, "en")
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                bot.send_message(chat_id, "Error during registration. Please try again. or Report to admin @yegna_tv")
            clear_user_state(chat_id)

    @bot.message_handler(func=lambda m: has_user_state(m.chat.id))
    def handle_post_flow(message: telebot.types.Message):
        chat_id = message.chat.id
        state = get_user_state(chat_id)
        if not state:
            return

        kind = state.get("kind")
        step = state.get("step")
        data = state.get("data", {})
        lang = get_user_lang(chat_id)

        if kind == "search" and step == "keyword":
            keyword = message.text.strip().lower()
            results = search_items(keyword)
            if not results:
                bot.send_message(chat_id, get_text("no_results", lang))
            else:
                for post in results:
                    bot.send_message(chat_id, format_post(post, lang))
            clear_user_state(chat_id)
            return

        if step == "title":
            data["title"] = message.text.strip()
            state["step"] = "description"
            set_user_state(chat_id, state)
            bot.send_message(chat_id, get_text("title_prompt", lang))
            return

        if step == "description":
            data["description"] = message.text.strip()
            state["step"] = "contact"
            set_user_state(chat_id, state)
            bot.send_message(chat_id, get_text("contact_prompt", lang))
            return

        if step == "contact":
            data["contact"] = message.text.strip()
            submit_post_for_review(bot, chat_id, kind, data)
            clear_user_state(chat_id)


def _show_settings(bot, message: telebot.types.Message):
    lang = get_user_lang(message.chat.id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton(get_text("english", lang), callback_data="lang_en"))
    markup.row(telebot.types.InlineKeyboardButton(get_text("amharic", lang), callback_data="lang_am"))
    markup.row(telebot.types.InlineKeyboardButton(get_text("afan_oromo", lang), callback_data="lang_om"))
    bot.send_message(message.chat.id, get_text("choose_language", lang), reply_markup=markup)
