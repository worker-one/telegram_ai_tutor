import logging.config
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import requests
from omegaconf import OmegaConf
from telebot.types import Message

from telegram_ai_tutor.db import crud
from telegram_ai_tutor.utils.html import extract_and_save_html

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_ai_tutor/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
base_url = config.service.base_url
strings = config.strings


def register_handlers(bot):
    # Step by step mode
    @bot.callback_query_handler(func=lambda call: call.data == "_step_by_step_mode")
    def step_by_step_mode(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].ask_query)
        bot.register_next_step_handler(call.message, _step_by_step_mode)

    @bot.message_handler(content_types=['text'], func=lambda message: message.text[0] != "/")
    def _step_by_step_mode(message: Message) -> None:
        user_id = int(message.chat.id)
        user_message = message.text

        # add user to database if not already present
        if not crud.get_user(user_id):
            logger.info(f"User with id {user_id} not found in the database.")
            crud.upsert_user(user_id, message.chat.username)

        # check if user exists in the database
        response = requests.get(f"{base_url}/users/{user_id}")
        if response.status_code == 404:
            # add user via api
            response = requests.post(
                f"{base_url}/users",
                json={
                    "user": {
                        "id": user_id,
                        "name": message.chat.username
                    }
                }
            )
            if response.status_code == 200:
                logger.info(f"User with id {user_id} added successfully.")
            else:
                logger.error(f"Error adding user with id {user_id}: {response.json()['message']}")

            # add a chat for this user
            response = requests.post(
                f"{base_url}/chats",
                json={
                    "user_id": user_id,
                    "chat_name": "default"
                }
            )
            if response.status_code == 200:
                response_json = response.json()
                logger.info(f"Chat for user with id {user_id} added successfully.")
                crud.upsert_user(user_id, last_chat_id=response_json['chat_id'])
            else:
                logger.error(f"Error adding chat for user with id {user_id}: {response.json()['message']}")

        last_chat_id = crud.get_last_chat_id(user_id)

        prompt = config.prompts[1]["prompt"]
        print(prompt)
        response = requests.post(
                f"{base_url}/model/query",
                json={
                    "user_id": user_id,
                    "chat_id": last_chat_id,
                    "user_message": prompt.format(user_message=user_message)
                }
            )
        response_content = response.json()["model_response"]["response_content"]
        try:
            # create tmp directory
            if not os.path.exists(f"./tmp/{user_id}"):
                os.makedirs(f"./tmp/{user_id}")
            extract_and_save_html(response_content, output_filename=f"./tmp/{user_id}/output.html")
            logger.info("HTML content extracted and saved successfully.")

            # Start a simple HTTP server to serve the HTML file
            class CustomHandler(SimpleHTTPRequestHandler):
                def translate_path(self, path):
                    # Serve files from the tmp directory
                    return os.path.join(os.getcwd(), 'tmp', path.lstrip('/'))

            def start_server():
                server_address = ('', 8000)  # Serve on all available interfaces, port 8000
                httpd = HTTPServer(server_address, CustomHandler)
                httpd.serve_forever()

            # Start the server in a new thread
            server_thread = threading.Thread(target=start_server)
            server_thread.daemon = True
            server_thread.start()

            # Provide the URL to the user
            response = strings.response.step_by_step.format(
                link=f"http://0.0.0.0:8000/{user_id}/output.html"
            )
            bot.reply_to(message, response)
        except:
            bot.reply_to(message, response_content, parse_mode="markdown")
