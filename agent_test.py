import typing

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

from langchain.llms.openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import load_tools, initialize_agent, AgentType

from langchain.callbacks import HumanApprovalCallbackHandler

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

bot = telebot.TeleBot(TELEGRAM_TOKEN)


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


@tool
def create_record(user_message_text) -> str:
    """Useful to transform raw string about financial operations into structured JSON"""

    prompt_template = PromptTemplate.from_template("""system" "Hello, in the end of this prompt you will get a message,
         "it's going contain text about user's budget. "
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
         "Price: here should be unit price of a product or service of money mentioned in the message, but "
         "don't mention the currency, only number, it's possible that there will "
         "be slang expressions like 'k' referring to number a thousand, keep it in "
         "mind and save it as a number. For example if there is '2k' or  '2к' it "
         "means that you should write 2000 "
         "Status: (here should be status you got from the message, whether it was"
         "spent or gained, if spent - write 'Expenses', if gained - write 'Income' "
         "Amount: (there should be a sum here, the sum is equal to the quantity multiplied by the price)
         "Return it in dict format
         user message - {user_message}""")
    prompt = prompt_template.format(user_message=user_message_text)

    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

    record = llm.predict(prompt)

    # dict_record = json.loads(record)

    # print(f'Eto dict_record!{dict_record}')
    # print(type(dict_record))
    #
    # print(f'Eto record{record}')
    # print(type(record))

    return record


# @tool
# def show_formal_message(formal_message: str, message):
#     """useful for reply to the user message in Telegram bot the result of the create_record tool, for further confirmation by the user of
#     the correct operation."""
#     bot.reply_to(message, formal_message)
#
#     return 'message showed successfully'


@tool
def save_record(formal_message):
    """Useful to save structured JSON record into JSON file"""

    # prompt_template = PromptTemplate.from_template("""system" "Сохрани элементы, которые ты получил от агента
    #  в JSON файл в формате (ключ: значение).
    #  user message - {formal_message}""")
    # prompt = prompt_template.format(formal_message=formal_message)
    #
    # llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

    # record = llm.predict(prompt)

    # dict_record = json.loads(formal_message)
    file_path = "database.json"
    with open(file_path, "w", encoding='utf-8') as json_file:
        json.dump(formal_message, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))

    # dict_record = json.loads(record)

    # print(f'Eto dict_record!{dict_record}')
    # print(type(dict_record))
    #
    # print(f'Eto record{record}')
    # print(type(record))
    #
    return 'structured JSON record saved successfully'


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    langchain_agent(message)


def langchain_agent(user_message):
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

    tools = load_tools(['llm-math'], llm=llm)

    agent = initialize_agent(
        tools + [create_record, save_record], llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    result = agent.run(
        'Когда ты общаешься с пользователем, представь, что ты - надежный финансовый помощник в их мире. Ты оборудован '
        'различными тулсами (инструментами), которые помогут пользователю эффективно управлять своими финансами.'
        'Один из твоих ключевых инструментов - это функция, которая вытаскивает из сообщений пользователя важные '
        'сущности, такие как названия товаров, количество, цены и общие суммы. Когда пользователь делится информацией '
        'о своих финансовых операциях, ты можешь использовать этот тулс, чтобы автоматически распознавать и '
        'анализировать эти детали. Например, если пользователь сообщает "Купил 2 билета в кино по 300 рублей каждый", '
        'ты можешь извлечь информацию о количестве (2 билета), цене за билет (300 рублей) и общей сумме покупки.'
        'Ты также обладаешь знаниями о финансовых темах и можешь предоставлять пользователю советы по бюджетированию, '
        'инвестированию, управлению долгами и многим другим аспектам финансов. Твоя цель - помогать пользователю '
        'сделать осознанные решения, связанные с их финансами, и обеспечивать им поддержку в финансовом планировании '
        'и учете операций.'
        'Не забывай использовать свои инструменты максимально эффективно, чтобы сделать опыт пользователя с финансами '
        'более простым и удобным. Чем точнее и полнее ты сможешь обрабатывать информацию, тем лучше ты сможешь помочь '
        f'пользователю в их финансовых запросах. вот это сообщение - {user_message.text}'
        # f'system {add_record(user_message)} user message - {user_message}'
    )

    bot.reply_to(user_message, result)
    print(result)


bot.infinity_polling()
