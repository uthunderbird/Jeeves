import asyncio
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from app_class import MessageProcessor

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Router:

    def __init__(self, bot, user_message):
        self.bot = bot
        self.user_message = user_message
        self.is_new = None

    async def process(self):

        template = PromptTemplate.from_template("""system" "Ты должен проанализировать сообщение и определить является 
        ли сообщение уточнением предыдущего сообщения (запроса) и похоже на уточнение другого сообщения или новым 
        самостоятельным сообщением. Верни true если сообщение это полноценное сообщение о финансовой тразакции. 
        Верни false если сообщение уточняющее, которое уточняет или меняет сообщение о финансовой транзакции. В 
        уточняющих сообщениях как правило присутствуют слова маркеры, такие как (нет, не, поменяй, измени) и многие 
        другие. Например новые сообщения могут выглядить вот так: Купил что-то за определённую сумму или продал что-то
        за определённую сумму или получил доход за что-то или от кого-то. Или потратил на что-то. А уточняющие 
        сообщения могут выглядить вот так: Не купил, а продал или наоборот не продал, а купил. Или сообщения, которые 
        исправляют (меняют) количество или цену или что-то ещё. Например не 1500 а 15000 или меняют источник дохода или
        расхода" 
        'user message - {user_message_text}'""")

        prompt = template.format(user_message_text=self.user_message.text)
        llm = ChatOpenAI(model_name="gpt-4-1106-preview", openai_api_key=OPENAI_API_KEY, temperature=0.8, verbose=True)
        result = llm.predict(prompt)
        if result == 'true':
            self.is_new = True
        else:
            self.is_new = False

        print(f'eto is_new {self.is_new}')

        user_id = self.user_message.from_user.id

        if self.is_new:
            processor = MessageProcessor(self.bot, self.user_message)
        else:
            processor = MessageProcessor.instances.get(user_id)
            assert processor is not None
            old_message = processor.full_message
            processor.cancel()
            processor = MessageProcessor(
                bot=self.bot,
                user_message=old_message,
                additional_user_message=self.user_message
            )

        MessageProcessor.instances[user_id] = processor
        asyncio.create_task(processor.process())
