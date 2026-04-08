import os, telebot

from database import get_items, get_user, search_items
from helpers import format_post, get_user_lang, is_user_member,ensure_user_registered, start_post_flow
from localization import get_text
from utils import user_states



def commands_register(bot):
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message):
        chat_id = message.chat.id
        # Check if user has joined the channel
        if not is_user_member(bot,chat_id):
            channel_username = os.getenv("CHANNEL_USERNAME")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}"))
            bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
            return
        telegram_id = chat_id
        user = get_user(telegram_id)
        if user is None:
            # Not registered, ask for phone
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button = telebot.types.KeyboardButton(get_text("share_phone_button", "en"), request_contact=True)
            markup.add(button)
            bot.send_message(chat_id, get_text("share_phone", "en"), reply_markup=markup)
            user_states[chat_id] = {"kind": "registration", "step": "phone"}
        else:
            # Already registered, show main menu
            lang = user.get("language") or "en"
            text = get_text("welcome", lang)
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
            markup.row(get_text("list", lang), get_text("search", lang))
            markup.row(get_text("post_lost", lang), get_text("post_found", lang))
            markup.row(get_text("settings", lang), get_text("help", lang))
            bot.send_message(chat_id, text, reply_markup=markup)


    @bot.message_handler(commands=["list"])
    def cmd_list(message: telebot.types.Message):
        chat_id = message.chat.id
        # Check if user has joined the channel
        if not is_user_member(bot, chat_id):
            channel_username = os.getenv("CHANNEL_USERNAME")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}"))
            bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
            return
        lang = get_user_lang(message.chat.id)
        posts = get_items()
        if not posts:
            bot.reply_to(message, get_text("no_posts", lang))
            return
        for p in posts:
            bot.send_message(message.chat.id, format_post(p, lang))


    @bot.message_handler(commands=["search"])
    def cmd_search(message: telebot.types.Message):
        chat_id = message.chat.id
        # Check if user has joined the channel
        if not is_user_member(bot, chat_id):
            channel_username = os.getenv("CHANNEL_USERNAME")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}"))
            bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
            return
        lang = get_user_lang(message.chat.id)
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, get_text("search_usage", lang))
            return
        keyword = parts[1].lower()
        results = search_items(keyword)
        if not results:
            bot.reply_to(message, get_text("no_results", lang))
            return
        for p in results:
            bot.send_message(message.chat.id, format_post(p, lang))

    @bot.message_handler(commands=["post_lost"])
    def cmd_post_lost(message: telebot.types.Message):
        chat_id = message.chat.id
        # Check if user has joined the channel
        if not is_user_member(bot, chat_id):
            channel_username = os.getenv("CHANNEL_USERNAME")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}"))
            bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
            return
        start_post_flow(message, "lost",bot)


    @bot.message_handler(commands=["post_found"])
    def cmd_post_found(message: telebot.types.Message):
        chat_id = message.chat.id
        # Check if user has joined the channel
        if not is_user_member(bot, chat_id):
            channel_username = os.getenv("CHANNEL_USERNAME")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel_username[1:]}"))
            bot.send_message(chat_id, "Please join our channel to use the bot.", reply_markup=markup)
            return
        start_post_flow(message, "found")

