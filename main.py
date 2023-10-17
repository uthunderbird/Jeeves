import telebot
import os
import json
import re
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from telebot import types

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

    send_save_buttons(message.chat.id)


def send_save_buttons(chat_id):
    markup_inline = types.InlineKeyboardMarkup()
    item_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
    item_no = types.InlineKeyboardButton(text='Нет', callback_data='no')

    markup_inline.add(item_yes, item_no)
    bot.send_message(chat_id, 'Записать данные?', reply_markup=markup_inline)


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    if call.data == 'yes':
        file_path = "database.json"
        with open(file_path, "w", encoding='utf-8') as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))
        bot.send_message(call.message.chat.id, 'Новые данные успешно записаны')
    elif call.data == 'no':
        data_list.pop()
        bot.send_message(call.message.chat.id, 'Данные не записаны')

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(call.message.chat.id, call.message.message_id)


bot.infinity_polling()
