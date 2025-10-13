import os
import logging
from dataclasses import dataclass
from typing import List

import telebot
import dotenv
from localization import get_text, get_supported_languages
from database import create_user, get_user_language, update_user_language, add_item, get_items, search_items, get_user

dotenv.load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN", "REPLACE_WITH_YOUR_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(API_TOKEN)

# Pending posts for admin approval
pending_posts = {}


@dataclass
class ItemPost:
    id: int
    kind: str  # 'lost' or 'found'
    title: str
    description: str
    location: str
    contact: str


# Demo data (in-memory) - now using database
# demo_posts: List[ItemPost] = [
#     ItemPost(1, "lost", "Black wallet", "Black leather wallet with ID", "Library", "@alice"),
#     ItemPost(2, "found", "Set of keys", "Bunch of keys with a blue fob", "Cafeteria", "@bob"),
#     ItemPost(3, "lost", "iPhone 12", "Black iPhone in a green case", "Bus 42", "+123456789"),
# ]


def format_post(post, lang: str) -> str:
    if isinstance(post, dict):
        return (
            f"{get_text('post', lang)} #{post.get('id', 'N/A')} — {post.get('type', '').upper()}\n"
            f"{get_text('title', lang)}: {post.get('item_name', '')}\n"
            f"{get_text('description', lang)}: {post.get('description', '')}\n"
            f"{get_text('contact', lang)}: {get_user_contact(post.get('user_telegram_id'))}"
        )
    else:
        # fallback for old ItemPost
        return (
            f"{get_text('post', lang)} #{post.id} — {post.kind.upper()}\n"
            f"{get_text('title', lang)}: {post.title}\n"
            f"{get_text('description', lang)}: {post.description}\n"
            f"{get_text('contact', lang)}: {post.contact}"
        )


def get_user_contact(telegram_id: int) -> str:
    """Get user contact info."""
    user = get_user(telegram_id)
    if user:
        return user.get('phone_number', '') or user.get('username', '') or str(telegram_id)
    return str(telegram_id)


def get_user_lang(chat_id: int) -> str:
    """Get user's language preference."""
    lang = get_user_language(chat_id)
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
    telegram_id = chat_id
    lang = get_user_language(telegram_id)
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
    lang = get_user_lang(message.chat.id)
    posts = get_items()
    if not posts:
        bot.reply_to(message, get_text("no_posts", lang))
        return
    for p in posts:
        bot.send_message(message.chat.id, format_post(p, lang))


@bot.message_handler(commands=["search"])
def cmd_search(message: telebot.types.Message):
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
    telegram_id = call.message.chat.id
    try:
        update_user_language(telegram_id, lang_code)
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
    user_id = post['user_id']
    if action == "approve":
        try:
            added_item = add_item(
                item_name=post['title'],
                description=post['description'],
                user_telegram_id=user_id,
                type=post['kind'],
                status='active'
            )
            if added_item and added_item.data:
                item_data = added_item.data[0]
                # Post to channel
                channel_username = os.getenv("CHANNEL_USERNAME")
                formatted_post = format_post(item_data, 'en')
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


@bot.message_handler(content_types=['contact'])
def handle_contact(message: telebot.types.Contact):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if state and state.get("kind") == "registration" and state.get("step") == "phone":
        phone = message.contact.phone_number
        telegram_id = chat_id
        username = message.from_user.username
        first_name = message.from_user.first_name
        try:
            create_user(telegram_id, username, first_name, phone)
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
        del user_states[chat_id]


@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_post_flow(message: telebot.types.Message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        return
    kind = state.get("kind")
    step = state.get("step")
    data = state.get("data", {})

    # Search flow
    lang = get_user_lang(chat_id)
    if kind == "search" and step == "keyword":
        keyword = message.text.strip().lower()
        results = search_items(keyword)
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
        state["step"] = "contact"
        bot.send_message(message.chat.id, get_text("contact_prompt", lang))
        return

    if step == "contact":
        data["contact"] = message.text.strip()
        # Send to admin for approval
        pending_id = f"{chat_id}_{len(pending_posts) + 1}"
        pending_posts[pending_id] = {
            'kind': kind,
            'title': data['title'],
            'description': data['description'],
            'contact': data['contact'],
            'user_id': chat_id
        }
        admin_id = int(os.getenv("ADMIN_ID"))
        formatted = f"New {kind} post:\nTitle: {data['title']}\nDescription: {data['description']}\nContact: {data['contact']}\nUser ID: {chat_id}"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("Approve", callback_data=f"approve_{pending_id}"),
            telebot.types.InlineKeyboardButton("Reject", callback_data=f"reject_{pending_id}")
        )
        bot.send_message(admin_id, formatted, reply_markup=markup)
        bot.send_message(message.chat.id, "Your post has been submitted for review.")
        del user_states[message.chat.id]


if __name__ == "__main__":
    if API_TOKEN == "REPLACE_WITH_YOUR_TOKEN":
        print("Please set TELEGRAM_TOKEN in the environment or .env before running the bot.")
    else:
        print("Starting Lost & Found bot (press Ctrl+C to stop)")
        bot.infinity_polling()