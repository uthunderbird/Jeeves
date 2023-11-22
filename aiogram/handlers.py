import asyncio
import logging

from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart
from main import HandleText
from config import dp, bot, router, llm
from main import WorkSpace
from langchain.chat_models import ChatOpenAI
from config import OPENAI_API_KEY
from aiogram import F


@dp.message(CommandStart())
async def send_welcome(msg: Message):
    await msg.reply(f"Howdy, how are you doing {msg.from_user.first_name}?")


@dp.message()
async def handle_text(msg: Message):
    commands_handler = HandleText(bot)
    await commands_handler.handle_text(msg)


# @dp.message(Command("report"))
# async def send_welcome(msg: Message):
#     commands_handler = SendJson(bot)
#     await commands_handler.send_json(msg)


@dp.callback_query(F.data == "yes")
async def handle_yes(callback: CallbackQuery):
    user_message = callback.message
    workspace = WorkSpace(bot)
    workspace.save_record(user_message)
    await user_message.edit_text('Data saved!')


@dp.callback_query(F.data == "no")
async def handle_no(callback: CallbackQuery):
    user_message = callback.message
    await user_message.edit_text('Data not saved!')


async def main(dp, bot):
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(main(dp, bot))