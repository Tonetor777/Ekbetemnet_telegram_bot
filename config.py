# config.py

import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DB_PATH = os.getenv("DB_PATH", "data/bot.db")  # Default value if not set