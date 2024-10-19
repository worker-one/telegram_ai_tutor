import logging
from omegaconf import OmegaConf
from telegram_ai_tutor.db import crud
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telebot import TeleBot

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/telegram_ai_tutor/conf/config.yaml")
strings = config.strings

# TODO: user sessions
user_sessions = {}

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

        if not crud.get_user(user_id):
            crud.upsert_user(user_id, username)
        if not user_sessions.get(user_id):
            user_sessions[user_id] = {}
            user_sessions[user_id]["lang"] = "en"

        user = crud.get_user(user_id)
        lang = user_sessions[user_id]["lang"]
        logger.info({"user_id": message.from_user.id, "message": message.text})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call):
        lang = "en"
        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].menu.language, reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_feedback")
    def feedback(call: CallbackQuery):
        user_id = call.from_user.id
        user = crud.get_user(user_id)
        lang = user_sessions[user_id]["lang"]
        logger.info({"user_id": call.from_user.id, "message": call.data})

        feedback_rating_markup = create_feedback_rating_markup()
        bot.send_message(call.message.chat.id, strings[lang].ask_feedback_rating, reply_markup=feedback_rating_markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_feedback_rating_"))
    def feedback_rating(call: CallbackQuery):
        user_id = call.from_user.id
        rating = int(call.data.split("_")[-1])
        lang = user_sessions[user_id]["lang"]

        bot.send_message(
            call.message.chat.id,
            strings[lang].ask_feedback_comment,
            reply_markup=create_skip_markup(strings[lang], rating)
        )
        bot.register_next_step_handler(call.message, save_feedback_comment, user_id, rating)

    def save_feedback_comment(message, user_id=None, rating=None):
        lang = user_sessions[user_id]["lang"]
        feedback_text = message.text if message.text.lower() != strings[lang].skip.lower() else None
        crud.save_feedback(user_id, rating, feedback_text)
        lang = user_sessions[user_id]["lang"]
        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].feedback_saved)
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_skip_"))
    def save_feedback_no_comment(call: CallbackQuery):
        user_id = call.from_user.id
        rating = int(call.data.split("_")[-1])
        lang = user_sessions[user_id]["lang"]
        crud.save_feedback(user_id, rating)
        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].feedback_saved)
        bot.send_message(
            call.message.chat.id,
            strings[lang].main_menu,
            reply_markup=main_menu_markup
        )
