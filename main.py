import os
import logging
from dataclasses import dataclass
from typing import List

import telebot
import dotenv
from localization import get_text, get_supported_languages
from database import create_user, get_user_language, update_user_language

dotenv.load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN", "REPLACE_WITH_YOUR_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(API_TOKEN)


@dataclass
class ItemPost:
    id: int
    kind: str  # 'lost' or 'found'
    title: str
    description: str
    location: str
    contact: str


# Demo data (in-memory)
demo_posts: List[ItemPost] = [
    ItemPost(1, "lost", "Black wallet", "Black leather wallet with ID", "Library", "@alice"),
    ItemPost(2, "found", "Set of keys", "Bunch of keys with a blue fob", "Cafeteria", "@bob"),
    ItemPost(3, "lost", "iPhone 12", "Black iPhone in a green case", "Bus 42", "+123456789"),
]


def format_post(post: ItemPost, lang: str) -> str:
    return (
        f"{get_text('post', lang)} #{post.id} — {post.kind.upper()}\n"
        f"{get_text('title', lang)}: {post.title}\n"
        f"{get_text('description', lang)}: {post.description}\n"
        f"{get_text('last_seen', lang)} / {get_text('found_at', lang)}: {post.location}\n"
        f"{get_text('contact', lang)}: {post.contact}"
    )


def get_user_lang(chat_id: int) -> str:
    """Get user's language preference."""
    lang = get_user_language(str(chat_id))
    return lang if lang else "en"


def ensure_user_registered(chat_id: int, message: telebot.types.Message):
    """Ensure user is registered in database."""
    user_id = str(chat_id)
    user = get_user_language(user_id)
    if user is None:  # assuming get_user_language returns None if not found
        username = message.from_user.username
        first_name = message.from_user.first_name
        try:
            create_user(user_id, username, first_name)
        except:
            pass  # ignore if already exists or error


# Simple flow state container (per-user, in-memory)
user_states = {}


def start_post_flow(message: telebot.types.Message, kind: str):
    ensure_user_registered(message.chat.id, message)
    lang = get_user_lang(message.chat.id)
    chat_id = message.chat.id
    user_states[chat_id] = {"kind": kind, "step": "title", "data": {}}
    bot.send_message(chat_id, get_text("creating_post", lang, kind=kind))


@bot.message_handler(commands=["start"])
def cmd_start(message: telebot.types.Message):
    chat_id = message.chat.id
    user_id = str(chat_id)
    lang = get_user_language(user_id)
    if lang is None:
        # Not registered, ask for phone
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = telebot.types.KeyboardButton(get_text("share_phone_button", "en"), request_contact=True)
        markup.add(button)
        bot.send_message(chat_id, get_text("share_phone", "en"), reply_markup=markup)
        user_states[chat_id] = {"kind": "registration", "step": "phone"}
    else:
        # Already registered, show main menu
        text = get_text("welcome", lang)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        markup.row(get_text("list", lang), get_text("search", lang))
        markup.row(get_text("post_lost", lang), get_text("post_found", lang))
        markup.row(get_text("settings", lang), get_text("help", lang))
        bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(commands=["list"])
def cmd_list(message: telebot.types.Message):
    ensure_user_registered(message.chat.id, message)
    lang = get_user_lang(message.chat.id)
    if not demo_posts:
        bot.reply_to(message, get_text("no_posts", lang))
        return
    for p in demo_posts:
        bot.send_message(message.chat.id, format_post(p, lang))


@bot.message_handler(commands=["search"])
def cmd_search(message: telebot.types.Message):
    ensure_user_registered(message.chat.id, message)
    lang = get_user_lang(message.chat.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, get_text("search_usage", lang))
        return
    keyword = parts[1].lower()
    results = [p for p in demo_posts if keyword in p.title.lower() or keyword in p.description.lower()]
    if not results:
        bot.reply_to(message, get_text("no_results", lang))
        return
    for p in results:
        bot.send_message(message.chat.id, format_post(p, lang))


@bot.message_handler(commands=["post_lost"])
def cmd_post_lost(message: telebot.types.Message):
    start_post_flow(message, "lost")


@bot.message_handler(commands=["post_found"])
def cmd_post_found(message: telebot.types.Message):
    start_post_flow(message, "found")


@bot.message_handler(func=lambda m: m.text and m.text in {
    get_text("list", get_user_lang(m.chat.id)),
    get_text("search", get_user_lang(m.chat.id)),
    get_text("post_lost", get_user_lang(m.chat.id)),
    get_text("post_found", get_user_lang(m.chat.id)),
    get_text("settings", get_user_lang(m.chat.id)),
    get_text("help", get_user_lang(m.chat.id))
})
def handle_button_press(message: telebot.types.Message):
    ensure_user_registered(message.chat.id, message)
    lang = get_user_lang(message.chat.id)
    text = message.text.strip()
    if text == get_text("list", lang):
        cmd_list(message)
        return
    if text == get_text("search", lang):
        # enter search state
        chat_id = message.chat.id
        user_states[chat_id] = {"kind": "search", "step": "keyword"}
        bot.send_message(chat_id, get_text("search_prompt", lang))
        return
    if text == get_text("post_lost", lang):
        start_post_flow(message, "lost")
        return
    if text == get_text("post_found", lang):
        start_post_flow(message, "found")
        return
    if text == get_text("settings", lang):
        show_settings(message)
        return
    if text == get_text("help", lang):
        cmd_start(message)
        return


def show_settings(message: telebot.types.Message):
    lang = get_user_lang(message.chat.id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton(get_text("english", lang), callback_data="lang_en"))
    markup.row(telebot.types.InlineKeyboardButton(get_text("amharic", lang), callback_data="lang_am"))
    markup.row(telebot.types.InlineKeyboardButton(get_text("afan_oromo", lang), callback_data="lang_om"))
    bot.send_message(message.chat.id, get_text("choose_language", lang), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_selection(call: telebot.types.CallbackQuery):
    lang_code = call.data[5:]  # remove "lang_"
    user_id = str(call.message.chat.id)
    try:
        update_user_language(user_id, lang_code)
        lang = lang_code
        bot.answer_callback_query(call.id, get_text("language_set", lang, language=get_text(lang_code, lang)))
        bot.edit_message_text(get_text("choose_language", lang), call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.error(f"Error updating language: {e}")
        bot.answer_callback_query(call.id, "Error setting language.")


@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_post_flow(message: telebot.types.Message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        return
    kind = state.get("kind")
    step = state.get("step")
    data = state.get("data", {})

    # Registration flow
    if kind == "registration" and step == "phone":
        if message.contact:
            phone = message.contact.phone_number
            user_id = str(chat_id)
            username = message.from_user.username
            first_name = message.from_user.first_name
            try:
                create_user(user_id, username, first_name, phone)
                bot.send_message(chat_id, get_text("registration_complete", "en"))
                # Now show main menu
                lang = "en"  # default
                text = get_text("welcome", lang)
                markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
                markup.row(get_text("list", lang), get_text("search", lang))
                markup.row(get_text("post_lost", lang), get_text("post_found", lang))
                markup.row(get_text("settings", lang), get_text("help", lang))
                bot.send_message(chat_id, text, reply_markup=markup)
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                bot.send_message(chat_id, "Error during registration. Please try again.")
        else:
            # Remind to share phone
            bot.send_message(chat_id, get_text("share_phone", "en"))
        del user_states[chat_id]
        return

    # Search flow
    lang = get_user_lang(chat_id)
    if kind == "search" and step == "keyword":
        keyword = message.text.strip().lower()
        results = [p for p in demo_posts if keyword in p.title.lower() or keyword in p.description.lower()]
        if not results:
            bot.send_message(message.chat.id, get_text("no_results", lang))
        else:
            for p in results:
                bot.send_message(message.chat.id, format_post(p, lang))
        del user_states[message.chat.id]
        return

    # Post creation flow
    if step == "title":
        data["title"] = message.text.strip()
        state["step"] = "description"
        bot.send_message(message.chat.id, get_text("title_prompt", lang))
        return

    if step == "description":
        data["description"] = message.text.strip()
        state["step"] = "location"
        bot.send_message(message.chat.id, get_text("description_prompt", lang))
        return

    if step == "location":
        data["location"] = message.text.strip()
        state["step"] = "contact"
        bot.send_message(message.chat.id, get_text("location_prompt", lang))
        return

    if step == "contact":
        data["contact"] = message.text.strip()
        # finalize
        new_id = max([p.id for p in demo_posts], default=0) + 1
        post = ItemPost(new_id, kind, data["title"], data["description"], data["location"], data["contact"])
        demo_posts.append(post)
        bot.send_message(message.chat.id, get_text("post_added", lang))
        bot.send_message(message.chat.id, format_post(post, lang))
        del user_states[message.chat.id]


if __name__ == "__main__":
    if API_TOKEN == "REPLACE_WITH_YOUR_TOKEN":
        print("Please set TELEGRAM_TOKEN in the environment or .env before running the bot.")
    else:
        print("Starting Lost & Found bot (press Ctrl+C to stop)")
        bot.infinity_polling()