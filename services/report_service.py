import logging
import os


logger = logging.getLogger(__name__)


def report_to_admin(bot, context: str, error):
    """Send a bug report to the admin chat if ADMIN_ID is configured."""
    admin_id_raw = os.getenv("ADMIN_ID")
    if not admin_id_raw:
        logger.warning("ADMIN_ID is not set; cannot report error.")
        return

    try:
        admin_id = int(admin_id_raw)
    except ValueError:
        logger.warning("ADMIN_ID is not a valid integer; cannot report error.")
        return

    error_text = f"{type(error).__name__}: {error}" if isinstance(error, Exception) else str(error)
    text = f"ERROR in {context}\n{error_text}"

    try:
        bot.send_message(admin_id, text)
    except Exception:
        logger.exception("Failed to send error report to admin.")
