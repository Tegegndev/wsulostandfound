#supabase database connection and functions

#users table name is botusers not users so use it not users

from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

client: Client = create_client(url, key)


def create_user(telegram_id: int, username: str = None, first_name: str = None, phone_number: str = None):
    """Create a new user in the database."""
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "phone_number": phone_number,
        "language": "en"  # default language
    }
    response = client.table("botusers").insert(data).execute()
    return response


def get_user(telegram_id: int):
    """Get user data by telegram_id."""
    try:
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
    response = client.table("botusers").update({"language": language}).eq("telegram_id", telegram_id).execute()
    return response


def get_user_language(telegram_id: int):
    """Get user's language preference. Returns None if user not registered."""
    try:
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
    response = client.table("items").insert(data).execute()
    return response


def get_items(type: str = None, status: str = 'active'):
    """Get items from the database."""
    try:
        query = client.table("items").select("*").eq("status", status)
        if type:
            query = query.eq("type", type)
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error retrieving items: {e}")
        return []


def search_items(keyword: str, type: str = None, status: str = 'active'):
    """Search items by keyword in item_name or description using database filtering."""
    try:
        # Sanitize keyword to prevent potential injection through special characters
        # Remove or escape special PostgREST filter characters
        safe_keyword = keyword.replace(',', ' ').replace('(', '').replace(')', '').replace('.', ' ')
        
        query = client.table("items").select("*").eq("status", status)
        if type:
            query = query.eq("type", type)
        # Use ilike for case-insensitive pattern matching
        # Search in item_name or description fields
        query = query.or_(f"item_name.ilike.%{safe_keyword}%,description.ilike.%{safe_keyword}%")
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error searching items: {e}")
        return []