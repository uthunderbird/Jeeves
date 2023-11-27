import asyncio

import telebot.async_telebot
import os
from dotenv import load_dotenv
from app_class import SendWelcome, HandleText, SendJson
# from report_generator import PDFGenerator

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.async_telebot.AsyncTeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    commands_handler = SendWelcome(bot)
    commands_handler.send_welcome(message)


@bot.message_handler(commands=['report'])
def send_report(message):
    user_id = message.from_user.id
    pdf_generator = PDFGenerator()
    pdf_filename = pdf_generator.generate_pdf_report(user_id)

    if pdf_filename:
        with open(pdf_filename, "rb") as pdf_file:
            bot.send_document(message.chat.id, pdf_file, caption="Financial Report")
        os.remove(pdf_filename)
    else:
        bot.reply_to(message, "Unable to generate the report.")


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    commands_handler = HandleText(bot)
    commands_handler.handle_text(message)


asyncio.run(bot.polling())
