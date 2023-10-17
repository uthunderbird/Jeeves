import telebot
import os
import json
import re
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

data_list = []


def add_record(entity, quantity, price, status):
    record = {
        "name": entity,
        "amount": quantity,
        "price": price,
        "total": status
    }
    data_list.append(record)


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message):
    bot.reply_to(message, f"Howdy, how are you doing {message.from_user.first_name}?")


@bot.message_handler(commands=['report'])
def send_json(message: telebot.types.Message):
    file_path = "database.json"
    if os.path.exists(file_path):
        with open(file_path, "rb") as json_file:
            bot.send_document(message.chat.id, json_file)
    else:
        bot.reply_to(message, "JSON файл не найден.")


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    global data_list

    template = PromptTemplate.from_template('выяви сущность (товар или услугу), выяви количество, выяви цену'
                                            'и выяви потратил деньги или заработал пользователь и ответь по такому '
                                            'шаблону Сущность: (тут сущность которую ты выявил), количество: (тут '
                                            'количество сущностей), Цена: (тут сумма денег которую потратил или '
                                            'заработал пользователь), Статус: (тут напиши заработал или потратил) из '
                                            'следующего сообщения - {text}')

    prompt = template.format(text=message.text)
    response_text = llm.predict(prompt)
    bot.reply_to(message, response_text)

    entity_match = re.search(r'Сущность: (.+)', response_text)
    quantity_match = re.search(r'Количество: (.+)', response_text)
    price_match = re.search(r'Цена: (.+)', response_text)
    status_match = re.search(r'Статус: (.+)', response_text)

    if entity_match and quantity_match and price_match and status_match:
        entity = entity_match.group(1)
        quantity = quantity_match.group(1)
        price = price_match.group(1)
        status = status_match.group(1)
        add_record(entity, quantity, price, status)

    file_path = "database.json"
    with open(file_path, "w", encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))

    print("Новые данные успешно записаны в файл:", file_path)


bot.infinity_polling()
