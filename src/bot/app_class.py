import functools
import typing
from asyncio import Event
from uuid import UUID

import _asyncio
import asyncio

import telebot.async_telebot
import os
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.human import HumanRejectedException
from budget.models.models import Session, Transaction
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from telebot import types
from langchain.agents import load_tools, initialize_agent, AgentType

from workers.chains.transaction_structurer import make_chain as make_structurer_chain

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class SendWelcome:
    def __init__(self, bot):
        self.bot = bot

    async def send_welcome(self, message: telebot.types.Message):
        await self.bot.reply_to(message, f"Howdy, how are you doing {message.from_user.first_name}?")


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


class MessageProcessor:
    instances = {}

    class CreateRecordSchema(BaseModel):
        user_message_text: str = Field(description='user original message text and additional message text')

    def __init__(self, bot, user_message, additional_user_message: telebot.types.Message | None = None):
        self.spaced_text = '; '
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

    def __getstate__(self):
        state = self.__dict__.copy()
        # Удаление объектов _asyncio.Future из состояния
        for key, value in list(state.items()):
            if isinstance(value, asyncio.Future):
                del state[key]
        for key in list(state.keys()):
            if isinstance(state[key], _asyncio.Future):
                del state[key]
        if '_answer_recieved' in state:
            del state['_answer_recieved']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._answer_recieved = asyncio.Event()

    def cancel(self):
        self.answerCall = False
        self._answer_recieved.set()

    async def process(self):

        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8, verbose=True)

        tools = load_tools(['llm-math'], llm=llm)

        callbacks = [HumanApprovalCallbackHandler(
            should_check=self._should_check,
            approve=self._approve
        )]

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
            'System: Когда ты общаешься с пользователем, представь, что ты - надежный финансовый помощник в их мире. '
            'Ты оборудован '
            'различными тулсами (инструментами), которые помогут пользователю эффективно управлять своими финансами.'
            'Один из твоих ключевых инструментов - это функция, которая вытаскивает из сообщений пользователя важные '
            'сущности, такие как названия товаров, количество, цены и общие суммы. Когда пользователь делится '
            'информацией '
            'о своих финансовых операциях, ты можешь использовать этот тулс, чтобы автоматически распознавать и '
            'анализировать эти детали. Например, если пользователь сообщает "Купил 2 билета в кино по 300 рублей '
            'каждый", '
            'ты можешь извлечь информацию о количестве (2 билета), цена за билет (300 рублей) и общей сумме покупки.'
            'Ты также обладаешь знаниями о финансовых темах и можешь предоставлять пользователю советы по '
            'бюджетированию, '
            'инвестированию, управлению долгами и многим другим аспектам финансов. Твоя цель - помогать пользователю '
            'сделать осознанные решения, связанные с их финансами, и обеспечивать им поддержку в финансовом '
            'планировании '
            'и учете операций.'
            'Не забывай использовать свои инструменты максимально эффективно, чтобы сделать опыт пользователя с '
            'финансами '
            'более простым и удобным. Чем точнее и полнее ты сможешь обрабатывать информацию, тем лучше ты сможешь '
            'помочь '
            f'пользователю в их финансовых запросах.'
            f'User: {self.text}',
            callbacks=callbacks
        )
        await self.bot.reply_to(self.user_message, result)
        return "Processed"

    def create_record(self, *args, **kwargs):
        """Useful to transform raw string about financial operations into structured JSON"""

        model = ChatOpenAI(model="gpt-4-turbo-preview")
        chain = make_structurer_chain(model)
        return chain.invoke({'message': self.text}).model_dump()

    def save_record(self, callable_: functools.partial | None = None, **data_dict):

        if callable_:
            return callable_()

        session = Session()

        financial_record = Transaction(
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

        markup_inline.add(item_yes)
        self.save_data_question_message = await self.bot.send_message(
            self.user_message.chat.id,
            'If everything is correct press "yes", else tell me what i should change',
            reply_markup=markup_inline,
        )

    def filter_callbacks(self, call: telebot.types.CallbackQuery):
        if self.save_data_question_message is None:
            return False
        return call.message.id == self.save_data_question_message.id

    async def answer_wrapper(self, call):
        if call.data == 'yes':
            await self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            await self.bot.delete_message(call.message.chat.id, call.message.message_id)
            self.answerCall = True
        elif call.data == 'no':
            await self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            await self.bot.delete_message(call.message.chat.id, call.message.message_id)
            self.answerCall = False
        self._answer_recieved.set()

    def build_answer_callback(self):
        @self.bot.callback_query_handler(func=self.filter_callbacks)
        async def answer_wrapper(call):
            await self.answer_wrapper(call)

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
        return self.answerCall
