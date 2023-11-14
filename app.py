import telebot
import os
from dotenv import load_dotenv
from app_class import SendWelcome, HandleText, SendJson

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    commands_handler = SendWelcome(bot)
    commands_handler.send_welcome(message)


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    commands_handler = HandleText(bot)
    commands_handler.handle_text(message)


@bot.message_handler(commands=['report'])
def send_welcome(message):
    commands_handler = SendJson(bot)
    commands_handler.send_json(message)


bot.infinity_polling()
