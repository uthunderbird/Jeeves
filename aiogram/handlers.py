from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode
from main import HandleText, SendJson
import config

router = config.router


@router.message(Command("start"))
async def send_welcome(msg: Message):
    await msg.answer(f"Howdy, how are you doing {msg.from_user.first_name}?")


@router.message(Command("text"))
async def handle_text(msg: Message):
    commands_handler = HandleText(config.bot)
    await commands_handler.handle_text(msg)


@router.message(Command("report"))
async def send_welcome(msg: Message):
    commands_handler = SendJson(config.bot)
    await commands_handler.send_json(msg)
