from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from database.requests import get_muted, add_muted, remove_muted, is_muted

router = Router()


@router.message(Command("mutedlist"))
async def get_muted_list(message: Message) -> None:
    muted_list = await get_muted(message.chat.id)
    text = "Пользователи в муте: \n " + "\n".join(
        [str(user.user_id) for user in muted_list]) if muted_list else 'Список пуст'
    await message.answer(text)


@router.message(Command("unmute"))
async def unmute(message: Message) -> None:
    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя")
        return
    if await is_muted(message.chat.id, message.reply_to_message.from_user.id):
        await remove_muted(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"Пользователь @{message.reply_to_message.from_user.username} размучен")
    else:
        await message.answer(f"Пользователь @{message.reply_to_message.from_user.username} не в муте")


@router.message(Command("mute"))
async def mute(message: Message) -> None:
    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя")
        return
    if not (await is_muted(message.chat.id, message.reply_to_message.from_user.id)):
        await add_muted(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"Пользователь @{message.reply_to_message.from_user.username} замучен")
    else:
        await message.answer(f"Пользователь @{message.reply_to_message.from_user.username} уже в муте")


@router.message(Command("kick"))
async def kick(message: Message, bot: Bot) -> None:
    if not message.reply_to_message:
        await message.answer("Ответьте на сообщение пользователя")
        return
    if not (await bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)).status in ['creator',
                                                                                                          'administrator',
                                                                                                          'left',
                                                                                                          'kicked']:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
