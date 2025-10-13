import os
import logging
from dataclasses import dataclass, asdict
from typing import List

import telebot

# Simple in-memory demo lost & found Telegram bot
# Uses pyTelegramBotAPI (TeleBot)

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


def format_post(post: ItemPost) -> str:
    return (
        f"Post #{post.id} — {post.kind.upper()}\n"
        f"Title: {post.title}\n"
        f"Description: {post.description}\n"
        f"Last seen / Found at: {post.location}\n"
        f"Contact: {post.contact}"
    )


@bot.message_handler(commands=["start"])
def cmd_start(message: telebot.types.Message):
    text = (
        "Welcome to the Lost & Found demo bot!\n\n"
        "Commands:\n"
        "/list - show demo posts\n"
        "/search <keyword> - search demo posts\n"
        "/post_lost - demo flow to add a lost item (text-only)\n"
        "/post_found - demo flow to add a found item (text-only)\n"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["list"])
def cmd_list(message: telebot.types.Message):
    if not demo_posts:
        bot.reply_to(message, "No posts available.")
        return
    for p in demo_posts:
        bot.send_message(message.chat.id, format_post(p))


@bot.message_handler(commands=["search"])
def cmd_search(message: telebot.types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /search <keyword>")
        return
    keyword = parts[1].lower()
    results = [p for p in demo_posts if keyword in p.title.lower() or keyword in p.description.lower()]
    if not results:
        bot.reply_to(message, "No matching posts found.")
        return
    for p in results:
        bot.send_message(message.chat.id, format_post(p))


# Simple flow state container (per-user, in-memory)
user_states = {}


def start_post_flow(message: telebot.types.Message, kind: str):
    chat_id = message.chat.id
    user_states[chat_id] = {"kind": kind, "step": "title", "data": {}}
    bot.send_message(chat_id, f"Creating a new {kind} post. What's the item title?")


@bot.message_handler(commands=["post_lost"])
def cmd_post_lost(message: telebot.types.Message):
    start_post_flow(message, "lost")


@bot.message_handler(commands=["post_found"])
def cmd_post_found(message: telebot.types.Message):
    start_post_flow(message, "found")


@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_post_flow(message: telebot.types.Message):
    state = user_states.get(message.chat.id)
    if not state:
        return
    step = state["step"]
    data = state["data"]

    if step == "title":
        data["title"] = message.text.strip()
        state["step"] = "description"
        bot.send_message(message.chat.id, "Please provide a short description of the item.")
        return

    if step == "description":
        data["description"] = message.text.strip()
        state["step"] = "location"
        bot.send_message(message.chat.id, "Where was it last seen / found?")
        return

    if step == "location":
        data["location"] = message.text.strip()
        state["step"] = "contact"
        bot.send_message(message.chat.id, "How can someone contact you? (username/phone/email)")
        return

    if step == "contact":
        data["contact"] = message.text.strip()
        # finalize
        new_id = max([p.id for p in demo_posts], default=0) + 1
        post = ItemPost(new_id, state["kind"], data["title"], data["description"], data["location"], data["contact"])
        demo_posts.append(post)
        bot.send_message(message.chat.id, "Thanks — your post has been added (demo only). Here it is:")
        bot.send_message(message.chat.id, format_post(post))
        del user_states[message.chat.id]


if __name__ == "__main__":
    if API_TOKEN == "REPLACE_WITH_YOUR_TOKEN":
        print("Please set TELEGRAM_TOKEN in the environment or .env before running the bot.")
    else:
        print("Starting demo Lost & Found bot (press Ctrl+C to stop)")
        bot.infinity_polling()
