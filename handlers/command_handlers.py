import telebot

from database import get_items, get_user, search_items
from helpers import format_post, get_user_lang, is_user_member, start_post_flow
from localization import get_text
from services.menu_service import send_join_channel_prompt, send_main_menu
from utils import set_user_state


def register_command_handlers(bot):
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return

        user = get_user(chat_id)
        if user is None:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button = telebot.types.KeyboardButton(get_text("share_phone_button", "en"), request_contact=True)
            markup.add(button)
            bot.send_message(chat_id, get_text("share_phone", "en"), reply_markup=markup)
            set_user_state(chat_id, {"kind": "registration", "step": "phone"})
            return

        lang = user.get("language") or "en"
        send_main_menu(bot, chat_id, lang)

    @bot.message_handler(commands=["list"])
    def cmd_list(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return

        lang = get_user_lang(chat_id)
        posts = get_items()
        if not posts:
            bot.reply_to(message, get_text("no_posts", lang))
            return
        for post in posts:
            bot.send_message(chat_id, format_post(post, lang))

    @bot.message_handler(commands=["search"])
    def cmd_search(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return

        lang = get_user_lang(chat_id)
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, get_text("search_usage", lang))
            return

        keyword = parts[1].lower()
        results = search_items(keyword)
        if not results:
            bot.reply_to(message, get_text("no_results", lang))
            return

        for post in results:
            bot.send_message(chat_id, format_post(post, lang))

    @bot.message_handler(commands=["post_lost"])
    def cmd_post_lost(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return
        start_post_flow(message, "lost", bot)

    @bot.message_handler(commands=["post_found"])
    def cmd_post_found(message: telebot.types.Message):
        chat_id = message.chat.id
        if not is_user_member(bot, chat_id):
            send_join_channel_prompt(bot, chat_id)
            return
        start_post_flow(message, "found", bot)
