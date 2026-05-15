import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "tasks.db")
PORT = int(os.getenv("PORT", 8000))
