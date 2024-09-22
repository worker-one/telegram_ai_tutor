import logging.config

import requests
from omegaconf import OmegaConf
from telebot import types

from telegram_llm_chatbot.db import crud

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_llm_chatbot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

cfg = OmegaConf.load("./src/telegram_llm_chatbot/conf/config.yaml")
base_url = cfg.service.base_url

logger.info(f"LLM service base url: {base_url}")


def register_handlers(bot):
    # Define the command for adding a chat
    # Ask for name of a new chat
    @bot.message_handler(commands=['add_chat'])
    def add_chat(message):
        user_id = int(message.chat.id)

        # add user to database if not already present
        if crud.get_user(user_id) is None:
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


        bot.reply_to(message, cfg.strings.add_chat_ask_name)
        bot.register_next_step_handler(message, _add_chat)

    def _add_chat(message):
        user_id = int(message.chat.id)
        chat_name = message.text

        # add chat for the user
        response = requests.post(
            f"{base_url}/chats",
            json={
                "user_id": user_id,
                "chat_name": chat_name
            }
        )
        if response.status_code == 200:
            bot.reply_to(message, cfg.strings.add_chat_success.format(chat_name=chat_name))
        else:
            bot.reply_to(message, cfg.strings.add_chat_error)
            bot.send_message(chat_id=user_id, text=response.json()["message"])

    @bot.message_handler(commands=['current_chat'])
    def current_chat(message):
        user_id = int(message.chat.id)

        # add user to database if not already present
        if crud.get_user(user_id) is None:
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

        chat_id = crud.get_last_chat_id(user_id)

        if chat_id:
            response = requests.get(
                f"{base_url}/chats/{user_id}",
                json={"user_id": user_id},
                timeout=10
            )
            chats = response.json()['chats']
            chat_name = [chat['chat_name'] for chat in chats if chat['chat_id'] == chat_id][0]
            bot.reply_to(message, cfg.strings.current_chat.format(chat_name=chat_name))
        else:
            bot.reply_to(message, cfg.strings.current_chat_no_chat)

    # Define the command for getting chats
    @bot.message_handler(commands=['get_chats'])
    def get_chats(message):
        user_id = int(message.chat.id)

        # add user to database if not already present
        if crud.get_user(user_id) is None:
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

        response = requests.get(
            f"{base_url}/chats/{user_id}",
            json={"user_id": user_id},
            timeout=15
        )
        chats = response.json()['chats']

        markup = types.InlineKeyboardMarkup()
        for chat in chats:
            button = types.InlineKeyboardButton(
                text=chat['chat_name'],
                callback_data=f"select_chat_{chat['chat_id']}_{chat['chat_name']}"
            )
            markup.add(button)

        if chats:
            bot.send_message(chat_id=message.chat.id, text=cfg.strings.get_chats, reply_markup=markup)
        else:
            bot.send_message(chat_id=message.chat.id, text=cfg.strings.get_chats_empty)


    @bot.callback_query_handler(func=lambda call: "select_chat_" in call.data)
    def select_chat_callback_query(call):
        chat_id = int(call.data.split('_')[2])
        chat_name = call.data.split('_')[3]
        user_id = call.from_user.id

        logging.info(f"User with id {user_id} selected chat `{chat_name}`.")

        try:
            # Update the last_chat_id for the user
            crud.upsert_user(user_id, call.from_user.username, last_chat_id=chat_id)
        except Exception as e:
            logger.error(f"Error updating user with id {user_id}: {e}")
            bot.send_message(
                chat_id=call.message.chat.id,
                text="An error occurred. Please try again later."
            )

        logger.info(f"User with id {user_id} updated successfully with chat_id {chat_id}.")
        # Send a message to the user
        bot.send_message(
            chat_id=call.message.chat.id,
            text=cfg.strings.handle_callback_query_success.format(chat_name=chat_name)
        )


    @bot.message_handler(commands=['delete_chat'])
    def delete_chat(message):
        user_id = int(message.chat.id)

        # add user to database if not already present
        if crud.get_user(user_id) is None:
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

        response = requests.post(
            f"{base_url}/chats",
            json={"user_id": user_id},
            timeout=10
        )
        chats = response.json()['chats']

        if not chats:
            bot.send_message(chat_id=message.chat.id, text=cfg.strings.get_chats_empty)
        else:
            markup = types.InlineKeyboardMarkup()
            for chat in chats:
                button = types.InlineKeyboardButton(
                    text=chat['chat_name'],
                    callback_data=f"delete_chat_{chat['chat_id']}_{chat['chat_name']}"
                )
                markup.add(button)

            bot.send_message(
                chat_id=message.chat.id,
                text=cfg.strings.delete_chat_ask,
                reply_markup=markup
            )


    @bot.callback_query_handler(func=lambda call: "delete_chat_" in call.data)
    def delete_chat_callback_query(call):
        user_id = int(call.from_user.id)
        chat_id = int(call.data.split('_')[2])
        chat_name = call.data.split('_')[3]

        response = requests.delete(
            f"{base_url}/chats/{user_id}/{chat_id}",
            timeout=10
        )
        if response.status_code == 200:
            bot.send_message(
                chat_id=user_id,
                text=cfg.strings.delete_chat_success.format(chat_name=chat_name)
            )
            # Propose to select another chat via /get_chats command
            response = requests.get(
                f"{base_url}/chats/{user_id}",
                timeout=10
            )
            chats = response.json()['chats']

            markup = types.InlineKeyboardMarkup()
            for chat in chats:
                button = types.InlineKeyboardButton(
                    text=chat['chat_name'],
                    callback_data=f"select_chat_{chat['chat_id']}_{chat['chat_name']}"
                )
                markup.add(button)

            if chats:
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text=cfg.strings.get_chats,
                    reply_markup=markup
                )
            else:
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text=cfg.strings.get_chats_empty
                )

        else:
            bot.send_message(
                chat_id=user_id,
                text=cfg.strings.delete_chat_error
            )
