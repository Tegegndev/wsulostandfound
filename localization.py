import json
import os
from typing import Dict, Any

LOCALES_DIR = os.path.join(os.path.dirname(__file__), 'locales')
locales: Dict[str, Dict[str, Any]] = {}

def load_locales():
    """Load all locale files."""
    global locales
    for filename in os.listdir(LOCALES_DIR):
        if filename.endswith('.json'):
            lang_code = filename[:-5]  # remove .json
            with open(os.path.join(LOCALES_DIR, filename), 'r', encoding='utf-8') as f:
                locales[lang_code] = json.load(f)

def get_text(key: str, lang: str = 'en', **kwargs) -> str:
    """Get localized text for a key."""
    if not locales:
        load_locales()
    locale = locales.get(lang, locales.get('en', {}))
    text = locale.get(key, f"[{key}]")  # fallback to key in brackets if not found
    return text.format(**kwargs) if kwargs else text

def get_supported_languages():
    """Get list of supported language codes."""
    if not locales:
        load_locales()
    return list(locales.keys())