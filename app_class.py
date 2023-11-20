import functools
import typing

import telebot
import os
import json
from models import Session, FinancialRecord
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from telebot import types
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType

from langchain.callbacks import HumanApprovalCallbackHandler

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)


class SendWelcome:
    def __init__(self, bot):
        self.bot = bot

    def send_welcome(self, message: telebot.types.Message):
        self.bot.reply_to(message, f"Howdy, how are you doing {message.from_user.first_name}?")


class HandleText:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def handle_text(message: telebot.types.Message):
        agent = WorkSpace(bot=bot)
        agent.langchain_agent(user_message=message)


class SendJson:
    def __init__(self, bot):
        self.bot = bot

    def send_json(self, message: telebot.types.Message):
        file_path = "database.json"
        if os.path.exists(file_path):
            with open(file_path, "rb") as json_file:
                self.bot.send_document(message.chat.id, json_file)
        else:
            self.bot.reply_to(message, "JSON not found.")


class WorkSpace:

    class SaveRecordSchema(BaseModel):
        product: str = Field(description='entity')
        price: int = Field(description='price')
        quantity: int = Field(description='quantity')
        status: str = Field(description='status')
        amount: int = Field(description='amount')

    class CreateRecordSchema(BaseModel):
        user_message_text: str = Field(description='user input text')
    def __init__(self, bot):
        self.bot = bot
        self.record = {}
        self.answerCall = True

    def langchain_agent(self, user_message: telebot.types.Message):
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8, verbose=True)

        tools = load_tools(['llm-math'], llm=llm)

        callbacks = [HumanApprovalCallbackHandler(should_check=self._should_check,
                                                  approve=functools.partial(self._approve,
                                                                            user_message=user_message))]

        agent = initialize_agent(
            tools + [
                # self.save_record,
                StructuredTool.from_function(
                    func=self.create_record,
                    name='create_record',
                    description="""Useful to transform raw string about financial operations into structured JSON""",
                    args_schema=self.CreateRecordSchema,
                ),
                # Tool.from_function(functools.partial(self.show_formal_message, user_message=user_message),
                #                    'show_formal_message',
                #                    """useful for reply to the user message in Telegram bot the result of the
                #                         create_record tool or for validation, for further confirmation by the user of
                #                         the correct operation. You need to use this tool immediately after
                #                         create_record tool and before save_record tool"""),
                StructuredTool.from_function(
                    func=self.save_record,
                    name='save_record',
                    description="""Useful to save structured dict record into JSON file""",
                    args_schema=self.SaveRecordSchema,
                )
        ], llm,
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
            'ты можешь извлечь информацию о количестве (2 билета), цена за билет (300 рублей) и общей сумме покупки.'
            'Ты также обладаешь знаниями о финансовых темах и можешь предоставлять пользователю советы по бюджетированию, '
            'инвестированию, управлению долгами и многим другим аспектам финансов. Твоя цель - помогать пользователю '
            'сделать осознанные решения, связанные с их финансами, и обеспечивать им поддержку в финансовом планировании '
            'и учете операций.'
            'Не забывай использовать свои инструменты максимально эффективно, чтобы сделать опыт пользователя с финансами '
            'более простым и удобным. Чем точнее и полнее ты сможешь обрабатывать информацию, тем лучше ты сможешь помочь '
            f'пользователю в их финансовых запросах. вот это сообщение - {user_message.text}',
            callbacks=callbacks
        )
        self.bot.reply_to(user_message, result)
        print(result)

    def create_record(self, user_message_text):
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
             user message - {user_message}""")

        prompt = prompt_template.format(user_message=user_message_text)
        llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY, temperature=0.8)
        record = llm.predict(prompt)

        # record = json.loads(record)
        self.record = record
        print(f'ETO SELF REC {self.record}')
        print(f'ETO REC {record}')
        print(type(self.record))
        print(type(record))
        return json.dumps(self.record)

    # def save_record(self, product, qty, price, status, total):
    def save_record(self, product, price, quantity, status, amount):
        session = Session()

        financial_record = FinancialRecord(
            product=product,
            quantity=quantity,
            status=status,
            amount=amount
        )

        session.add(financial_record)
        session.commit()

        session.close()

        return 'Structured JSON record saved successfully'

    def send_save_buttons(self, chat_id):
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')
        item_no = types.InlineKeyboardButton(text='No', callback_data='no')

        markup_inline.add(item_yes, item_no)
        self.bot.send_message(chat_id, 'Save data?', reply_markup=markup_inline)

    @bot.callback_query_handler(func=lambda call: True)
    def answer(self, call):
        if call.data == 'yes':
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                               reply_markup=None)
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
            self.answerCall = True
            return True
        elif call.data == 'no':
            self.answerCall = False
            return False

    @staticmethod
    def _should_check(serialized_obj: dict) -> bool:
        return serialized_obj.get("name") == "save_record"

    def _approve(self, _input: dict, user_message) -> bool:
        print(f'ETO INPUT {_input}')
        print(type(_input))
        print(f'ETO USER_MESSAGE {user_message}')
        print(type(user_message))
        # if 'formal_message' in _input:
        #     return True
        msg = (
            "Do you approve of the following input? "
            "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
        )
        msg += _input
        self.bot.reply_to(user_message, msg)
        self.send_save_buttons(user_message.chat.id)
        # resp = self.answer()
        # return resp.lower() in ("yes", "y")
        return self.answerCall


# class CallbackQueryHandler:
#     def __init__(self, bot):
#         self.bot = bot
#
#     def send_save_buttons(self, chat_id):
#         markup_inline = types.InlineKeyboardMarkup()
#         item_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')
#         item_no = types.InlineKeyboardButton(text='No', callback_data='no')
#
#         markup_inline.add(item_yes, item_no)
#         self.bot.send_message(chat_id, 'Save data?', reply_markup=markup_inline)
#
#     @staticmethod
#     def _should_check(serialized_obj: dict) -> bool:
#         return serialized_obj.get("name") == "save_record"
#
#     def _approve(self, _input: str, user_message) -> bool:
#         print(f'ETO INPUT {_input}')
#         print(type(_input))
#         print(f'ETO USER_MESSAGE {user_message}')
#         print(type(user_message))
#         # if 'formal_message' in _input:
#         #     return True
#         msg = (
#             "Do you approve of the following input? "
#             "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
#         )
#         msg += "\n\n" + _input + "\n"
#         self.bot.reply_to(user_message, msg)
#         CallbackQueryHandler.send_save_buttons(user_message.chat.id)
#         resp = input(msg)
#         return resp.lower() in ("yes", "y")


    # def show_formal_message(self, formal_message: str, user_message):
    #     """useful for reply to the user message in Telegram bot the result of the create_record tool or for validation,
    #     for further confirmation by the user of the correct operation. You need to use this tool immediately after
    #     create_record tool and before save_record tool """
    #     self.bot.reply_to(user_message, formal_message)
    #
    #     return 'message showed successfully'
