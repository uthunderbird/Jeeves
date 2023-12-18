import asyncio
import functools
import typing

from asyncio import Event
from uuid import UUID

import telebot.async_telebot
import os
import json

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.human import HumanRejectedException

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

# from routerV2 import Router

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class SendWelcome:
    def __init__(self, bot):
        self.bot = bot

    def send_welcome(self, message: telebot.types.Message):
        self.bot.reply_to(message, f"Howdy, how are you doing {message.from_user.first_name}?")


# class HandleText:
#     def __init__(self, bot):
#         self.bot = bot
#
#     async def handle_text(self, message: telebot.types.Message):
#         agent = Router(bot=self.bot, user_message=message)
#         await agent.process()
#         # pass


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


class HumanApprovalCallbackHandler(AsyncCallbackHandler):
    """Callback for manually validating values."""

    raise_error: bool = True

    def __init__(
        self,
        approve,
        should_check: typing.Callable[[typing.Dict[str, typing.Any]], bool],
    ):
        self._approve = approve
        self._should_check = should_check

    async def on_tool_start(
        self,
        serialized: typing.Dict[str, typing.Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: typing.Optional[UUID] = None,
        **kwargs: typing.Any,
    ) -> typing.Any:
        if self._should_check(serialized) and not await self._approve(input_str):
            raise HumanRejectedException(
                f"Inputs {input_str} to tool {serialized} were rejected."
            )


# class MessageProcessorRepository:
#
#     def __init__(self):
#         pass
#
#     def get_by_user_id(self, user_id: int) -> 'MessageProcessor' | None:
#         pass
#
#     def create_by_user_id(self, user_id: int) -> 'MessageProcessor':
#         pass
#
#     def extend_by_user_id(self, user_id, new_message: telebot.types.Message):
#         pass


#TODO реализовать сколейку не текста, а фулл сообщения


class MessageProcessor:
    instances = {}

    # def __new__(cls, bot, user_message, additional_user_message=None):
    #     user_id = user_message.from_user.id
    #     if user_id not in cls.instances:
    #         instance = super(MessageProcessor, cls).__new__(cls)
    #         cls.instances[user_id] = instance
    #         return instance
    #     return cls.instances[user_id]

    class SaveRecordSchema(BaseModel):
        product: str = Field(description='entity')
        price: int = Field(description='price')
        quantity: int = Field(description='quantity')
        status: str = Field(description='status')
        amount: int = Field(description='amount')

    class CreateRecordSchema(BaseModel):
        user_message_text: str = Field(description='user original message text and additional message text')
        print(f'ETO SCHEMA {user_message_text}')
        # text

    def __init__(self, bot, user_message, additional_user_message: telebot.types.Message | None = None):
        self.spaced_text = ' '
        if not hasattr(self, 'is_initialized'):
            self.bot = bot
            self.record = {}
            self.answerCall = True
            self._answer_recieved = Event()
            self.build_answer_callback()
            self.user_message = user_message
            self.save_data_question_message = None
            self.additional_user_messages = []
            self.is_initialized = True
            self.text = self.user_message.text
            self.full_message = self.user_message

        self.additional_user_message = additional_user_message

        if self.additional_user_message:
            self.text += self.additional_user_message.text
            self.full_message.text += " "
            self.full_message.text += self.additional_user_message.text

    def cancel(self):
        self.answerCall = False
        self._answer_recieved.set()

    async def process(self):

        # print(f'ETO INSTANCES {MessageProcessor.instances}')
        # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
        # print(f'ETO ADDITIONAL MESSAGE {self.additional_user_message}')
        # if self.additional_user_message:
        #     print(f'ETO ADDITIONAL MESSAGE TEXT {self.additional_user_message.text}')
        # print(f'ETO SELF TEXT {self.text}')
        #
        # if self.additional_user_message:
        #     self.spaced_text += self.additional_user_message.text
        #     self.text += self.spaced_text
        #     self.full_message.text += " "
        #     self.full_message.text += self.additional_user_message.text
        # print(f'ETO SELF TEXT2 {self.text}')
        # print(f'ETO FULL MESSAGE TEXT {self.full_message.text}')

        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8, verbose=True)

        tools = load_tools(['llm-math'], llm=llm)

        callbacks = [HumanApprovalCallbackHandler(should_check=self._should_check,
                                                  approve=self._approve)]

        agent = initialize_agent(
            tools + [
                StructuredTool.from_function(
                    func=self.create_record,
                    name='create_record',
                    description="""Useful to transform raw string about financial operations into structured JSON""",
                    args_schema=self.CreateRecordSchema,
                ),
                StructuredTool.from_function(
                    func=self.save_record,
                    name='save_record',
                    description="""Useful to save structured dict record into JSON file""",
                    args_schema=self.SaveRecordSchema,
                ),
        ], llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

        result = await agent.arun(
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
            f'пользователю в их финансовых запросах. вот это сообщение - {self.text}.',
            callbacks=callbacks
        )
        await self.bot.reply_to(self.user_message, result)
        # print(f'ETO INSTANCES {MessageProcessor.instances}')
        # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
        # if self.additional_user_message:
        #     print(f'ETO ADDITIONAL MESSAGE TEXT {self.additional_user_message.text}')
        # print(f'ETO SELF TEXT {self.text}')
        # print(result)
        # print(f'ETO INSTANCES {MessageProcessor.instances}')
        # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
        # print(f'ETO ADDITIONAL MESSAGE {self.additional_user_message}')
        # if self.additional_user_message:
        #     print(f'ETO ADDITIONAL MESSAGE TEXT {self.additional_user_message.text}')
        # print(f'ETO SELF TEXT {self.text}')
        # await self._answer_recieved.wait()
        return "Processed"

    def create_record(self, *args, **kwargs):
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
             "Amount: (there should be a sum here, the sum is equal to the quantity multiplied by the price),
             'user message - {text}'""")

        prompt = prompt_template.format(text=self.text)
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8)
        record = llm.predict(prompt)

        self.record = record
        record_dict = json.dumps(record)
        self.record = record_dict
        return record_dict

    def save_record(self, callable_: functools.partial | None = None, **data_dict):

        if callable_:
            return callable_()

        session = Session()

        financial_record = FinancialRecord(
                user_id=self.full_message.from_user.id,
                username=self.full_message.from_user.username,
                user_message=self.full_message.text,
                product=data_dict.get("product"),
                price=data_dict.get("price"),
                quantity=data_dict.get("quantity"),
                status=data_dict.get("status"),
                amount=data_dict.get("amount")
            )

        session.add(financial_record)
        session.commit()
        session.close()

        return 'Structured JSON record saved successfully'

    async def send_save_buttons(self):
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')
        item_no = types.InlineKeyboardButton(text='No', callback_data='no')

        markup_inline.add(item_yes, item_no)
        self.save_data_question_message = await self.bot.send_message(
            self.user_message.chat.id, 
            'Save data?', 
            reply_markup=markup_inline,
        )

    def filter_callbacks(self, call: telebot.types.CallbackQuery):
        return call.message.id == self.save_data_question_message.id

    def build_answer_callback(self):
        @self.bot.callback_query_handler(func=self.filter_callbacks)
        async def answer(call):
            if call.data == 'yes':
                print('YES')
                # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
                # print(f'ETO ADDITIONAL MESSAGE {self.additional_user_message}')
                await self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   reply_markup=None)
                await self.bot.delete_message(call.message.chat.id, call.message.message_id)
                self.answerCall = True 
            elif call.data == 'no':
                print('NO')
                # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
                # print(f'ETO ADDITIONAL MESSAGE {self.additional_user_message}')
                await self.bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                         message_id=call.message.message_id,
                                                         reply_markup=None)
                await self.bot.delete_message(call.message.chat.id, call.message.message_id)
                self.answerCall = False
            self._answer_recieved.set()

    @staticmethod
    def _should_check(serialized_obj: dict) -> bool:
        return serialized_obj.get("name") == "save_record"

    async def _approve(self, _input: str) -> bool:

        msg = (
            "Do you approve of the following input? "
            "Anything except 'Y'/'Yes' (case-insensitive) will be treated as a no."
        )
        input_dict = eval(_input)

        msg += _input

        formatted_message = (
            f"🛒 Product: {input_dict['product']}\n"
            f"🔢 Quantity: {input_dict['quantity']}\n"
            f"💲 Price: {input_dict['price']}\n"
            f"📉 Status: {input_dict['status']}\n"
            f"💰 Amount: {input_dict['amount']}"
        )

        chat_id = self.user_message.chat.id
        await self.bot.send_message(chat_id, formatted_message)   
        await self.send_save_buttons()
        await self._answer_recieved.wait()
        # print(f'ETO ADDITIONAL MESSAGES {self.additional_user_messages}')
        # print(f'ETO ADDITIONAL MESSAGE {self.additional_user_message}')
        return self.answerCall
