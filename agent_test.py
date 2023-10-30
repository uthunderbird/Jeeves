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

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

data_list = []


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
def add_record(user_message):
    """system" "Hello, in the end of this prompt you will get a message,
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
         user message - {user_message}"""
    record = {
        "record_id": 'record_id',
        "original_message": 'original_message',
        "name": 'entity',
        "quantity": 'quantity',
        "price": 'price',
        "total": 'status',
        "amount": 'amount',
        "timestamp": 'datetime.now().strftime("%Y-%m-%d %H:%M:%S")'
    }

    data_list.append(record)


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    pass


def langchain_agent():
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)

    tools = load_tools(['llm-math', 'add_record'], llm=llm)

    agent = initialize_agent(
        tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
    )

    result = agent.run(
        'What is average age of a dog? Multiply the age by 3'
    )

    print(result)


if __name__ == "__main__":
    # print(generate_pet_name('cat', 'orange'))
    langchain_agent()
