from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("udar"))
async def udar(message: Message, bot: Bot):
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name} ударил(а) по еб*лу {message.reply_to_message.from_user.first_name}')


@router.message(Command("kiss"))
async def kiss(message: Message, bot: Bot):
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name} поцеловал(а) {message.reply_to_message.from_user.first_name}')


@router.message(Command("sex"))
async def sex(message: Message, bot: Bot):
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name} трахнул(а) {message.reply_to_message.from_user.first_name}')


@router.message(Command("hug"))
async def hug(message: Message, bot: Bot):
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name} обнял(а) {message.reply_to_message.from_user.first_name}')


@router.message(Command("byk"))
async def byk(message: Message, bot: Bot):
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name} быканул(а) на {message.reply_to_message.from_user.first_name}')
