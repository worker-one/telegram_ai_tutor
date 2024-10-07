import logging.config
import os
import threading
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler

import requests
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
from telebot.types import Message

from telegram_ai_tutor.api.handlers.common import download_file, prepare_prompt, register_user_and_chat
from telegram_ai_tutor.utils.html import extract_and_save_html

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
base_url = os.getenv("LLM_API")
strings = config.strings

load_dotenv(find_dotenv(usecwd=True))

# Retrieve environment variables
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "_step_by_step_mode")
    def step_by_step_mode(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})

        bot.send_message(call.message.chat.id, strings["en"].ask_query)
        bot.register_next_step_handler(call.message, _step_by_step_mode)

    @bot.message_handler(content_types=['text', 'photo', 'document'], func=lambda message: message.text[0] != "/")
    def _step_by_step_mode(message: Message) -> None:
        user = register_user_and_chat(int(message.chat.id), message.chat.username)
        bot.send_message(message.chat.id, f"Your request has been received.")
        if message.content_type in ["photo", "document"]:
            prompt = prepare_prompt(message, config.prompts[1]["prompt_text"], config.prompts[1]["prompt_image"])
            file_id = message.photo[-1].file_id if message.content_type == "photo" else message.document.file_id
            user_input_image_path = f"./.tmp/photos/{file_id}"
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
            prompt = config.prompts[1]["prompt_text"].format(user_message=message.text)
            data = {"user_id": user.user_id, "chat_id": user.last_chat_id, "user_message": prompt}
            response = requests.post(f"{base_url}/model/query", data=data)

        if response.status_code == 200:
            response_content = response.json()["model_response"]["response_content"]
            if not os.path.exists(f"./.tmp/html/{user.user_id}"):
                if not os.path.exists("./.tmp/html"):
                    os.makedirs("./.tmp/html")
                os.makedirs(f"./.tmp/html/{user.user_id}")
            output_html_name = f"output_{uuid.uuid4()}.html"
            extract_and_save_html(response_content, output_filename=f"./.tmp/html/{user.user_id}/{output_html_name}")
            logger.info("HTML content extracted and saved successfully.")

            class CustomHandler(SimpleHTTPRequestHandler):
                def translate_path(self, path):
                    return os.path.join(os.getcwd(), '.tmp', path.lstrip('/'))

            def start_server():
                server_address = ("", int(PORT))
                httpd = HTTPServer(server_address, CustomHandler)
                httpd.serve_forever()

            # Start server in a daemon thread
            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()

            response = strings[user.language].response.step_by_step.format(
                link=f"{HOST}:{PORT}/html/{user.user_id}/{output_html_name}"
            )
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, f"Error querying model: {response.text}")
