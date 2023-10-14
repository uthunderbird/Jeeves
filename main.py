import telebot

import os
from dotenv import load_dotenv

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-3.5-turbo",
                 openai_api_key=OPENAI_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message):
    bot.reply_to(message, f"Howdy, how are you doing {message.from_user.first_name}?")


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    template = PromptTemplate.from_template('выяви сущность (товар или услугу), выяви количество, выяви цену'
                                            'и выяви потратил деньги или заработал пользователь и ответь по такому '
                                            'шаблону Сущность: (тут сущность которую ты выявил), количество: (тут '
                                            'количество сущностей), Цена: (тут сумма денег которую потратил или '
                                            'заработал пользователь), Статус: (тут напиши заработал или потратил) из '
                                            'следующего сообщения - {text}')

    prompt = template.format(text=message.text)
    response_text = llm.predict(prompt)
    bot.reply_to(message, response_text)


bot.infinity_polling()
