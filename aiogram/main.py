import asyncio
import logging
from config import bot, dp, router, OPENAI_API_KEY, TELEGRAM_TOKEN
import functools
import os
import json
from aiogram.types import Message
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain.callbacks import HumanApprovalCallbackHandler
from aiogram import types, Bot, Dispatcher


class HandleText:
    def __init__(self, bot):
        self.bot = bot

    async def handle_text(self, message: Message):
        agent = WorkSpace(bot=self.bot)
        await agent.langchain_agent(user_message=message)


class SendJson:
    def __init__(self, bot):
        self.bot = bot

    async def send_json(self, message: Message):
        file_path = "database.json"
        if os.path.exists(file_path):
            with open(file_path, "rb") as json_file:
                await self.bot.send_document(message.chat.id, json_file)
        else:
            await self.bot.send_message(message, "JSON not found.")


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
        self.markup_inline = None

    async def langchain_agent(self, user_message: Message):
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
        if await self._approve(result, user_message):
            await self.bot.send_message(user_message.chat.id, 'Data will be saved.')
        else:
            await self.bot.send_message(user_message.chat.id, 'Data will not be saved.')

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
    def save_record(
        self,
        product: str,
        price: int,
        quantity: int,
        status: str,
        amount: int,
    ) -> str:
        """Useful to save record in string format into JSON file"""

        file_path = "database.json"

        # Проверяем наличие файла и создаем его, если он не существует
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding='utf-8') as json_file:
                json.dump([], json_file, ensure_ascii=False, indent=4, separators=(',', ': '))

        # Пытаемся загрузить существующие данные из файла
        try:
            with open(file_path, "r", encoding='utf-8') as json_file:
                data = json.load(json_file)
        except json.decoder.JSONDecodeError:
            # Если файл пуст или содержит некорректный JSON, создаем пустой список
            data = []

        # Добавляем новую запись в список
        data.append({
            "product": product,
            "price": price,
            "quantity": quantity,
            "status": status,
            "amount": amount,
        })

        # Записываем обновленный список в файл
        with open(file_path, "w", encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4, separators=(',', ': '))

        return 'Structured JSON record saved successfully'

    async def send_with_inline_keyboard(self, chat_id):
        item_save = types.InlineKeyboardButton(text='Yes', callback_data='yes')
        item_cancel = types.InlineKeyboardButton(text='No', callback_data='no')
        self.markup_inline = types.InlineKeyboardMarkup(row_width=2, inline_keyboard=[[item_cancel], [item_save]])

        msg = (
            "Do you want to save the following data? "
            "Type 'Yes' to confirm or 'No' to cancel."
        )
        await self.bot.send_message(chat_id, msg, reply_markup=self.markup_inline)

    @staticmethod
    def _should_check(serialized_obj: dict) -> bool:
        return serialized_obj.get("name") == "save_record"

    async def _approve(self, _input: dict, user_message: Message) -> bool:
        print(f'ETO INPUT {_input}')
        print(type(_input))
        print(f'ETO USER_MESSAGE {user_message}')
        print(type(user_message))

        # msg = (
        #     "Do you want to save the following data? "
        #     "Type 'Yes' to confirm or 'No' to cancel."
        # )
        # await self.bot.send_message(user_message.chat.id, msg)

        await self.send_with_inline_keyboard(user_message.chat.id)

        response = await self.bot.wait_for(types.CallbackQuery, timeout=30)
        if response.data == 'yes':
            self.answerCall = True
        else:
            self.answerCall = False

        return self.answerCall

