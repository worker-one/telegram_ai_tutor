import logging.config
import os

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf

from telegram_ai_tutor.api.handlers import chats, menu, short, step_by_step

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error("BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

cfg = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")

# Define the base URL of your API
base_url = os.getenv("LLM_API")


def start_bot():
    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    chats.register_handlers(bot)
    menu.register_handlers(bot)
    short.register_handlers(bot)
    step_by_step.register_handlers(bot)
    bot.infinity_polling()
    #bot.polling()
