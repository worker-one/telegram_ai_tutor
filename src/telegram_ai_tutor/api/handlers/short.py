import logging.config

import requests
from omegaconf import OmegaConf
from telebot.types import Message

from telegram_ai_tutor.api.handlers.common import (
    download_file,
    handle_model_response,
    prepare_prompt,
    register_user_and_chat,
)
from telegram_ai_tutor.utils.json import extract_json_from_text

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
base_url = config.service.base_url
strings = config.strings

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "_short_mode")
    def short_mode(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        bot.send_message(call.message.chat.id, strings["en"].ask_query)
        bot.register_next_step_handler(call.message, _short_mode)

    @bot.message_handler(content_types=['text', 'photo', 'document'], func=lambda message: message.text[0] != "/")
    def _short_mode(message: Message) -> None:
        user = register_user_and_chat(int(message.chat.id), message.chat.username)

        if message.content_type in ["photo", "document"]:
            prompt = prepare_prompt(message, config.prompts[0]["prompt_text"], config.prompts[0]["prompt_image"])
            file_id = message.photo[-1].file_id if message.content_type == "photo" else message.document.file_id
            user_input_image_path = f"./.tmp/photos/{user.user_id}/{file_id}"
            try:
                download_file(bot, file_id, user_input_image_path)
                files = {"file": open(user_input_image_path, "rb")}
                data = {"user_id": user.user_id, "chat_id": user.last_chat_id, "user_message": prompt}
                response = requests.post(f"{base_url}/model/query", files=files, data=data)
            except Exception as e:
                logger.error(f"Error downloading image: {e}")
                bot.reply_to(message, f"Error downloading image: {e}")
                return
        else:
            prompt = config.prompts[0]["prompt_text"].format(user_message=message.text)
            data = {"user_id": user.user_id, "chat_id": user.last_chat_id, "user_message": prompt}
            response = requests.post(f"{base_url}/model/query", data=data)

        handle_model_response(bot, message, response, extract_json_from_text)
