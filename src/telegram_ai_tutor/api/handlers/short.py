import logging.config
import os

import requests
from omegaconf import OmegaConf
from telebot.types import Message

from telegram_ai_tutor.db import crud
from telegram_ai_tutor.utils.json import extract_json_from_text

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

    # Short mode
    @bot.callback_query_handler(func=lambda call: call.data == "_short_mode")
    def short_mode(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].ask_query)
        bot.register_next_step_handler(call.message, _short_mode)

    @bot.message_handler(
        content_types=['text', 'photo', 'document'],
        func=lambda message: message.text[0] != "/"
    )
    def _short_mode(message: Message) -> None:

        user_id = int(message.chat.id)
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

        if message.content_type == "photo":
            if message.text:
                user_message = message.text
            elif message.caption:
                user_message = message.caption
            else:
                user_message = "the problem is ine the image"
            prompt = config.prompts[0]["prompt"]

            try:
                # Get the file ID and download the image
                file_id = message.photo[0].file_id
                file_info = bot.get_file(file_id)
                file_path = file_info.file_path

                # Download the image
                downloaded_file = bot.download_file(file_path)

                # Save the image locally
                if not os.path.exists("./.tmp/photos"):
                    os.makedirs("./.tmp/photos")

                user_input_image_path = f"./.tmp/{file_path}"
                with open(user_input_image_path, "wb") as file:
                    file.write(downloaded_file)

                # Prepare the image and message for sending
                files = {"file": open(user_input_image_path, "rb")}
                data = {
                    "user_id": user_id,
                    "chat_id": last_chat_id,
                    "user_message": prompt.format(user_message=user_message)
                }

                # Send the request with the image file
                response = requests.post(
                    f"{base_url}/model/query",
                    files=files,  # Send image file
                    data=data    # Send other form data
                )

            except Exception as e:
                logger.error(f"Error downloading image: {e}")
                bot.reply_to(message, f"Error downloading image: {e}")
                return

        # if a photo sent as a document
        elif message.content_type == "document":
            if message.text:
                user_message = message.text
            elif message.caption:
                user_message = message.caption
            else:
                user_message = "the problem is ine the image"

            prompt = config.prompts[0]["prompt"]

            try:
                # Get the file ID and download the image
                file_id = message.document.file_id
                file_info = bot.get_file(file_id)
                file_path = file_info.file_path

                # Download the image
                downloaded_file = bot.download_file(file_path)

                # Save the image locally
                if not os.path.exists("./.tmp/photos"):
                    os.makedirs("./.tmp/photos")

                user_input_image_path = f"./.tmp/photos/{file_path}"
                with open(user_input_image_path, "wb") as file:
                    file.write(downloaded_file)

                # Prepare the image and message for sending
                files = {"file": open(user_input_image_path, "rb")}
                data = {
                    "user_id": user_id,
                    "chat_id": last_chat_id,
                    "user_message": prompt.format(user_message=user_message)
                }

                # Send the request with the image file
                response = requests.post(
                    f"{base_url}/model/query",
                    files=files,  # Send image file
                    data=data    # Send other form data
                )
            except Exception as e:
                logger.error(f"Error downloading image: {e}")
                bot.reply_to(message, f"Error downloading image: {e}")
                return


        # Handling text content
        else:
            user_message = message.text
            prompt = config.prompts[0]["prompt"]

            # Prepare the text message for sending
            data = {
                "user_id": user_id,
                "chat_id": last_chat_id,
                "user_message": prompt.format(user_message=user_message)
            }

            # Send the request with only the text data
            response = requests.post(
                f"{base_url}/model/query",
                json=data  # Send JSON if it's only a text request
            )

        # Get response content and handle it
        if response.status_code == 200:
            response_content = response.json()["model_response"]["response_content"]
            try:
                json_content = extract_json_from_text(response_content)
                bot.reply_to(message, json_content["answer"], parse_mode="markdown")
            except:
                bot.reply_to(message, response_content, parse_mode="markdown")
        else:
            bot.reply_to(message, "Error querying model")
