from telegram_ai_tutor.api.bot import start_bot
from telegram_ai_tutor.db.database import create_tables, drop_tables

if __name__ == "__main__":
    drop_tables()
    create_tables()
    start_bot()
