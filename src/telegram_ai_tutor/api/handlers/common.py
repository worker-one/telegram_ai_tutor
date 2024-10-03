import logging
import os

import requests
from omegaconf import OmegaConf
from telebot.types import Message

from telegram_ai_tutor.db import crud, models

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
base_url = config.service.base_url
strings = config.strings

def register_user_and_chat(user_id: int, username: str) -> models.User:
    if not crud.get_user(user_id):
        logger.info(f"User with id {user_id} not found in the database.")
        crud.upsert_user(user_id, username=username, last_chat_id=1)

    response = requests.get(f"{base_url}/users/{user_id}")
    if response.status_code == 404:
        response = requests.post(
            f"{base_url}/users",
            json={"user": {"id": user_id, "name": username}}
        )
        if response.status_code == 200:
            logger.info(f"User with id {user_id} added successfully.")
        else:
            logger.error(f"Error adding user with id {user_id}: {response.json()['message']}")

        response = requests.post(
            f"{base_url}/chats",
            json={"user_id": user_id, "chat_name": "default"}
        )
        if response.status_code == 200:
            response_json = response.json()
            logger.info(f"Chat for user with id {user_id} added successfully.")
            crud.upsert_user(user_id, username=username, last_chat_id=1)
        else:
            logger.error(f"Error adding chat for user with id {user_id}: {response.json()['message']}")
    # Fetch and return the user instance
    user = crud.get_user(user_id)
    return user

def download_file(bot, file_id, file_path):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, "wb") as file:
        file.write(downloaded_file)
    return file_path

def prepare_prompt(message: Message, prompt_text: str, prompt_image: str):
    if message.text:
        return prompt_text.format(user_message=message.text)
    elif message.caption:
        return prompt_text.format(user_message=message.caption)
    else:
        return prompt_image

def handle_model_response(bot, message: Message, response, extract_json_from_text=None):
    if response.status_code == 200:
        response_content = response.json()["model_response"]["response_content"]
        if extract_json_from_text:
            try:
                json_content = extract_json_from_text(response_content)
                bot.reply_to(message, json_content["answer"], parse_mode="markdown")
            except:
                bot.reply_to(message, response_content, parse_mode="markdown")
        else:
            bot.reply_to(message, response_content, parse_mode="markdown")
    else:
        bot.reply_to(message, f"Error querying model: {response.text}")