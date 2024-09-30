import logging.config

import requests
from omegaconf import OmegaConf
from telebot import TeleBot


# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


cfg = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
base_url = cfg.service.base_url


def register_handlers(bot: TeleBot):
    # Define the command for getting users
    @bot.message_handler(commands=['get_users'])
    def get_users(message):
        response = requests.get(f"{base_url}/users")
        bot.reply_to(message, f"Users: {response.json()}")
