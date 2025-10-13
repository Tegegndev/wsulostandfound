#supabase database connection and functions

from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

client: Client = create_client(url, key)


def create_user(user_id: str, username: str = None, first_name: str = None, phone_number: str = None):
    """Create a new user in the database."""
    data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "phone_number": phone_number,
        "language": "en"  # default language
    }
    response = client.table("users").insert(data).execute()
    return response


def get_user(user_id: str):
    """Get user data by user_id."""
    try:
        response = client.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving user: {e}")
        return None


def update_user_language(user_id: str, language: str):
    """Update user's language preference."""
    response = client.table("users").update({"language": language}).eq("user_id", user_id).execute()
    return response


def get_user_language(user_id: str):
    """Get user's language preference. Returns None if user not registered."""
    try:
        response = client.table("botusers").select("language").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0].get("language", "en")
        return None  # not registered
    except:
        return None