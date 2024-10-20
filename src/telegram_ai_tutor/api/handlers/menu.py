import logging

from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from telegram_ai_tutor.db import crud

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
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
        InlineKeyboardButton(strings.menu.change_language, callback_data="_change_language"),  # New button
    )
    return menu_markup

def create_lang_menu_markup(strings):
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings.language_en, callback_data="_en"),
        InlineKeyboardButton(strings.language_ru, callback_data="_ru")
    )
    return lang_menu_markup

def create_feedback_rating_markup():
    feedback_rating_markup = InlineKeyboardMarkup(row_width=5)
    buttons = [InlineKeyboardButton(str(i), callback_data=f"_feedback_rating_{i}") for i in range(1, 6)]
    feedback_rating_markup.add(*buttons)
    return feedback_rating_markup

def create_skip_markup(strings, rating: int):
    skip_markup = InlineKeyboardMarkup(row_width=1)
    skip_markup.add(InlineKeyboardButton(strings.skip, callback_data=f"_skip_{rating}"))
    return skip_markup

def register_handlers(bot: TeleBot):
    @bot.message_handler(commands=["menu"])
    def main_menu_command(message):
        user_id = message.from_user.id
        username = message.from_user.username

        user = crud.get_user(user_id)
        if not user:
            crud.upsert_user(user_id, username)
            user = crud.get_user(user_id)
        
        lang = user.lang
        logger.info({"user_id": message.from_user.id, "message": message.text})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call):
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.lang
        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].menu.language, reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_feedback")
    def feedback(call: CallbackQuery):
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.lang
        logger.info({"user_id": call.from_user.id, "message": call.data})

        feedback_rating_markup = create_feedback_rating_markup()
        bot.send_message(call.message.chat.id, strings[lang].ask_feedback_rating, reply_markup=feedback_rating_markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_feedback_rating_"))
    def feedback_rating(call: CallbackQuery):
        user_id = call.from_user.id
        rating = int(call.data.split("_")[-1])
        user = crud.get_user(user_id)
        lang = user.lang

        bot.send_message(
            call.message.chat.id,
            strings[lang].ask_feedback_comment,
            reply_markup=create_skip_markup(strings[lang], rating)
        )
        bot.register_next_step_handler(call.message, save_feedback_comment, user_id, rating)

    def save_feedback_comment(message, user_id=None, rating=None):
        user = crud.get_user(user_id)
        lang = user.lang
        feedback_text = message.text if message.text.lower() != strings[lang].skip.lower() else None
        crud.save_feedback(user_id, rating, feedback_text)
        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].feedback_saved)
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_skip_"))
    def save_feedback_no_comment(call: CallbackQuery):
        user_id = call.from_user.id
        rating = int(call.data.split("_")[-1])
        user = crud.get_user(user_id)
        lang = user.lang
        crud.save_feedback(user_id, rating)
        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].feedback_saved)
        bot.send_message(
            call.message.chat.id,
            strings[lang].main_menu,
            reply_markup=main_menu_markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_change_language")  # New handler
    def change_language(call: CallbackQuery):
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user.lang
        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].menu.language, reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data in ["_en", "_ru"])  # New handler
    def set_language(call: CallbackQuery):
        user_id = call.from_user.id
        new_lang = call.data.strip("_")
        crud.update_user_language(user_id, new_lang)
        user = crud.get_user(user_id)
        lang = user.lang
        logger.info({"user_id": call.from_user.id, "message": call.data})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].language_updated)
        bot.send_message(call.message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)