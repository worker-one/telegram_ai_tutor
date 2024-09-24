import logging.config
import os

import requests
import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf

from telegram_ai_tutor.api.handlers import chats, menu, short, step_by_step, users
from telegram_ai_tutor.db import crud
from telegram_ai_tutor.src.telegram_ai_tutor.api.handlers import step_by_step

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_ai_tutor/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error("BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

cfg = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")

# Define the base URL of your API
base_url = cfg.service.base_url

@bot.message_handler(commands=["help"])
def help_command(message):
    user_id = message.from_user.id

    # add user to database if not already present
    if crud.get_user(user_id) is None:
        crud.upsert_user(user_id, message.chat.username)

        # add user via api
        response = requests.post(
            f"{base_url}/add_user",
            json={
                "user": {
                    "id": user_id,
                    "name": message.chat.username
                }
            }
        )

    bot.reply_to(message, cfg.strings.help)


def start_bot():
    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    chats.register_handlers(bot)
    users.register_handlers(bot)
    menu.register_handlers(bot)
    short.register_handlers(bot)
    step_by_step.register_handlers(bot)
    #bot.infinity_polling()
    bot.polling()
