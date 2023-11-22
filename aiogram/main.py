import ast
import asyncio
import functools
from aiogram.types import Message
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain.callbacks import HumanApprovalCallbackHandler
from aiogram import types
from models import Session, FinancialRecord
from config import llm, dp


class HandleText:
    def __init__(self, bot):
        self.bot = bot
        self.workspace = WorkSpace(bot)

    async def handle_text(self, message: Message):
        return await self.workspace.langchain_agent(user_message=message)


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
        self.record = ''
        self.response_data = {}
        self.llm = llm
        self.markup_inline = None
        self.keyboard = None

    async def langchain_agent(self, user_message: Message):
        tools = load_tools(['llm-math'], llm=self.llm)

        callbacks = [HumanApprovalCallbackHandler(should_check=self._should_check,
                                                  approve=functools.partial(self._approve,
                                                                            user_message=user_message))]

        agent = initialize_agent(
            tools + [
                StructuredTool.from_function(
                    func=self.create_record,
                    name='create_record',
                    description="""Useful to transform raw string about financial operations into structured dictionary""",
                    args_schema=self.CreateRecordSchema,
                ),
            ], self.llm,
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

        await self._approve(_input=result, user_message=user_message)

        return result

    def create_record(self, user_message_text):
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
        record = llm.predict(prompt)
        self.record = record

        record_lines = record.split('\n')
        record_dict = {}

        for line in record_lines:
            key, value = map(str.strip, line.split(':'))
            record_dict[key] = value

        if record_dict:
            self.response_data = {
                "Product": record_dict.get('Product', ''),
                "Quantity": record_dict.get('Quantity', ''),
                "Price": record_dict.get('Price', ''),
                "Status": record_dict.get('Status', ''),
                "Amount": record_dict.get('Amount', '')
            }

        return self.response_data

    def save_record(self, user_message) -> str:

        if self.response_data:
            session = Session()

            try:
                financial_record = FinancialRecord(
                    user_id=user_message.from_user.id,
                    username=user_message.from_user.username,
                    user_message=user_message.text,
                    product=self.response_data.get("product"),
                    price=self.response_data.get("price"),
                    quantity=self.response_data.get("quantity"),
                    status=self.response_data.get("status"),
                    amount=self.response_data.get("amount")
                )

                session.add(financial_record)
                session.commit()
            except Exception as e:
                print(f"Error while saving financial record: {e}")
                session.rollback()
            finally:
                session.close()

            return 'Structured record saved successfully'

    def send_with_inline_keyboard(self):
        buttons = [
            [
                types.InlineKeyboardButton(text="Yes", callback_data="yes"),
                types.InlineKeyboardButton(text="No", callback_data="no")
            ],
        ]
        self.keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        return "Do you want to save the following data? Type 'Yes' to confirm or 'No' to cancel.", self.keyboard

    @staticmethod
    def _should_check(serialized_obj: dict) -> bool:
        return serialized_obj.get("name") == "save_record"

    async def _approve(self, _input: str, user_message):
        print(f'ETO INPUT {_input}')
        print(type(_input))
        print(f'ETO USER_MESSAGE {user_message}')
        print(type(user_message))

        text, keyboard = self.send_with_inline_keyboard()
        await user_message.reply(text=self.record)
        await user_message.answer(text=text, reply_markup=keyboard)



