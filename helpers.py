import os
import logging
import time
import telebot
from database import create_user, get_user, get_user_language
from localization import get_text
from utils import set_user_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANG_CACHE_TTL_SECONDS = 1200
_lang_cache = {}

def format_post(post, lang: str) -> str:
    if isinstance(post, dict):
        return (
            f"New {post.get('type', '').upper()} Post\n"
            f"<a href='tg://user?id={post.get('user_telegram_id')}'>"
            #f"{get_text('post', lang)} #{post.get('id', 'N/A')} — {post.get('type', '').upper()}\n"
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
    now = time.time()
    cached = _lang_cache.get(chat_id)
    if cached and cached[1] > now:
        return cached[0]

    lang = get_user_language(chat_id)
    resolved_lang = lang if lang else "en"
    _lang_cache[chat_id] = (resolved_lang, now + LANG_CACHE_TTL_SECONDS)
    return resolved_lang


def invalidate_user_lang_cache(chat_id: int):
    """Invalidate cached language for a user."""
    _lang_cache.pop(chat_id, None)


def is_user_member(bot,chat_id: int) -> bool:
    """Check if user is a member of the required channel."""
    channel_username = os.getenv("CHANNEL_USERNAME")
    try:
        member = bot.get_chat_member(channel_username, chat_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False


def ensure_user_registered(chat_id: int, message: telebot.types.Message):
    """Ensure user is registered in database."""
    user_id = chat_id
    user = get_user(user_id)
    if user is None:
        username = message.from_user.username
        first_name = message.from_user.first_name
        try:
            create_user(user_id, username, first_name)
        except Exception:
            logger.exception("Error ensuring user registration")


def start_post_flow(message: telebot.types.Message, kind: str,bot):
    ensure_user_registered(message.chat.id, message)
    lang = get_user_lang(message.chat.id)
    chat_id = message.chat.id
    set_user_state(chat_id, {"kind": kind, "step": "title", "data": {}})
    bot.send_message(chat_id, get_text("creating_post", lang, kind=kind))


