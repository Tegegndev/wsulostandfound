#supabase database connection and functions

#users table name is botusers not users so use it not users

from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Read env vars once
url: Optional[str] = os.getenv("SUPABASE_URL")
key: Optional[str] = os.getenv("SUPABASE_KEY")

# Lazy client initialization to avoid creating the Supabase client at import time.
# This gives clearer error messages if env vars are missing and avoids unexpected
# initialization side-effects (helpful during testing/imports).
_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is not None:
        return _client

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in the environment or .env file."
        )

    _client = create_client(url, key)
    return _client


def create_user(telegram_id: int, username: str = None, first_name: str = None, phone_number: str = None):
    """Create a new user in the database."""
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "phone_number": phone_number,
        "language": "en"  # default language
    }
    client = get_client()
    response = client.table("botusers").insert(data).execute()
    return response


def get_user(telegram_id: int):
    """Get user data by telegram_id."""
    try:
        client = get_client()
        response = client.table("botusers").select("*").eq("telegram_id", telegram_id).execute()
        if response.data:
            return response.data[0]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None


def update_user_language(telegram_id: int, language: str):
    """Update user's language preference."""
    client = get_client()
    response = client.table("botusers").update({"language": language}).eq("telegram_id", telegram_id).execute()
    return response


def get_user_language(telegram_id: int):
    """Get user's language preference. Returns None if user not registered."""
    try:
        client = get_client()
        response = client.table("botusers").select("language").eq("telegram_id", telegram_id).execute()
        if response.data:
            return response.data[0].get("language", "en")
        return None  # not registered
    except:
        return None


def add_item(item_name: str, description: str, user_telegram_id: int, type: str, item_image: str = None, status: str = 'active', telegram_message_id: int = None):
    """Add a new item to the database."""
    data = {
        "item_name": item_name,
        "description": description,
        "user_telegram_id": user_telegram_id,
        "type": type,
        "status": status,
        "telegram_message_id": telegram_message_id
    }
    if item_image:
        data["item_image"] = item_image
    client = get_client()
    response = client.table("items").insert(data).execute()
    return response


def get_items(type: str = None, status: str = 'active'):
    """Get items from the database."""
    try:
        client = get_client()
        query = client.table("items").select("*").eq("status", status)
        if type:
            query = query.eq("type", type)
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error retrieving items: {e}")
        return []


def search_items(keyword: str, type: str = None, status: str = 'active'):
    """Search items by keyword in item_name or description."""
    try:
        items = get_items(type, status)
        keyword_lower = keyword.lower()
        results = [
            item for item in items
            if keyword_lower in item.get('item_name', '').lower() or keyword_lower in item.get('description', '').lower()
        ]
        return results
    except Exception as e:
        print(f"Error searching items: {e}")
        return []