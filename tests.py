import telebot
import os
import json
import re
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from telebot import types
from datetime import datetime
from langchain.agents import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function

from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser

from langchain.schema.agent import AgentFinish
from langchain.agents import AgentExecutor

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

data_list = []

emoji_dict = {
    "Product": "🛒",
    "Quantity": "🔢",
    "Price": "💲",
    "Status": "📉",
    "Amount": "💰"
}


@tool
def add_record(entity, quantity, price, status, amount, original_message, record_id):
    """Сохранить элементы, которые ты получил из сообщения пользователя в следующем формате, и добавить в список
    для дальнейшей записи в JSON файл"""
    record = {
        "record_id": record_id,
        "original_message": original_message,
        "name": entity,
        "quantity": quantity,
        "price": price,
        "total": status,
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data_list.append(record)


tools = [add_record]


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
        bot.reply_to(message, "JSON not found.")


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    global data_list

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Hello, in the end of this prompt you will get a message, "
         "it's gonna contain text about user's budget. "
         "You should identify 4 parameters in this text: "
         "first is entity (product or service if it's about spending money) "
         "or source if it's about gaining money, "
         "second is the quantity of products, "
         "third is the amount of money gained or spent on this product, "
         "fourth is status gained/spent. "
         "Your answer should be like this: "
         "Product: (here should be the product or service you identified from the message "
         "or source of money if it was gained) "
         "Quantity: (here should be quantity of products or if there is no quantity "
         "you should fill 1 in here) "
         "Price: (here should be unit price of a product or service of money mentioned in the message, but "
         "don't mention the currency, only number, it's possible that there will "
         "be slang expressions like 'k' referring to number thousand, keep it in "
         "mind and save it as a number. For example if there is '2k' or  '2к' it "
         "means that your should write 2000) "
         "Status: (here should be status you got from the message, whether it was"
         "spent or gained, if spent - write 'Expenses', if gained - write 'Income' "
         "Amount: (there should be a sum here, the sum is equal to the quantity multiplied by the price)"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(t) for t in tools]
    )

    agent = {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_functions(x['intermediate_steps'])
            } | prompt | llm_with_tools | OpenAIFunctionsAgentOutputParser()

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    agent_executor.invoke({"input": message.text})
    print(data_list)
    result_string = ""
    for item in data_list:
        for key, value in item.items():
            result_string += f'{key}: {value}\n'

    bot.reply_to(message, result_string)
    send_save_buttons(message.chat.id)


def send_save_buttons(chat_id):
    markup_inline = types.InlineKeyboardMarkup()
    item_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')
    item_no = types.InlineKeyboardButton(text='No', callback_data='no')

    markup_inline.add(item_yes, item_no)
    bot.send_message(chat_id, 'Save data?', reply_markup=markup_inline)


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    if call.data == 'yes':
        file_path = "database.json"
        with open(file_path, "w", encoding='utf-8') as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))
        bot.send_message(call.message.chat.id, 'New data saved successfully')
    elif call.data == 'no':
        data_list.pop()

    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(call.message.chat.id, call.message.message_id)


bot.infinity_polling()
