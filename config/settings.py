import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY не задан в .env")
