from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.weather import get_weather

router = Router()


@router.message(Command("getinfo"))
async def get_user_info(message: Message):
    await message.answer(
        f"Информация о пользователе:\n"
        f"Имя: {message.reply_to_message.from_user.first_name} {message.reply_to_message.from_user.last_name}\n"
        f"Ник: {message.reply_to_message.from_user.username}\n"
        f"ID: {message.reply_to_message.from_user.id}")


@router.message(Command("chatinfo"))
async def get_chat_info(message: Message):
    await message.answer(
        f"Информация о чате:\n"
        f"ID: {message.chat.id}\n"
        f"Тип: {message.chat.type}")


@router.message(Command("weather"))
async def weather(message: Message) -> None:
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажи город: /weather Москва")
        return

    data = await get_weather(args[1])
    if not data:
        await message.answer("Город не найден")
        return

    await message.answer(
        f"Город: {data['name']}\n"
        f"Температура: {data['main']['temp']}°C\n"
        f"Ощущается как: {data['main']['feels_like']}°C\n"
        f"Погода: {data['weather'][0]['description']}"
    )
