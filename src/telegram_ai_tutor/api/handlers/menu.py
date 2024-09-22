import logging.config
from ast import In
from turtle import up

from omegaconf import OmegaConf
from telegram_ai_tutor.db import crud
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_ai_tutor/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
strings = config.strings

def create_main_menu_markup(strings):
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.menu.short_mode, callback_data="_short_mode"),
        InlineKeyboardButton(strings.menu.step_by_step_mode, callback_data="_step_by_step_mode"),
        InlineKeyboardButton(strings.menu.billing, callback_data="_billing"),
        InlineKeyboardButton(strings.menu.feedback, callback_data="_feedback"),
    )
    return menu_markup

def create_lang_menu_markup(strings):
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings.language_en, callback_data="_en"),
        InlineKeyboardButton(strings.language_ru, callback_data="_ru")
    )
    return lang_menu_markup


def register_handlers(bot):
    @bot.message_handler(commands=["menu"])
    def menu_menu_command(message):

        user_id = message.from_user.id
        username = message.from_user.username
        # add user to database if not already present
        if not crud.get_user(user_id):
            logger.info(f"User with id {user_id} not found in the database.")
            crud.upsert_user(user_id, message.chat.username)

        user = crud.get_user(user_id)
        lang = user.language
        logger.info({"user_id": message.from_user.id, "message": message.text})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    # Language selection
    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call):
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.language
        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, "Language", reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_ru")
    def language_ru(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username

        crud.upsert_user(user_id, username, language="ru")
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].language_selected)

    @bot.callback_query_handler(func=lambda call: call.data == "_en")
    def language_en(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username

        crud.upsert_user(user_id, username, language="en")
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].language_selected)

    # Useful links
    @bot.callback_query_handler(func=lambda call: call.data == "_feedback")
    def useful_links(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].useful_links)

    # Help
    @bot.callback_query_handler(func=lambda call: call.data == "_support")
    def support(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].support)

