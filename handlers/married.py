from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatFullInfo
from aiogram.filters.callback_data import CallbackData
from database.requests import get_married, get_married_in_chat, delete_married, set_married
from aiogram.exceptions import TelegramAPIError
from database.models import Married

router = Router()


class MarriedCallback(CallbackData, prefix="married"):
    choice: str
    chat_id: int
    married1: int
    married2: int


@router.callback_query(MarriedCallback.filter())
async def marry_callback(call: CallbackQuery, callback_data: MarriedCallback, bot: Bot):
    if call.from_user.id != callback_data.married2:
        return
    if callback_data.choice == 'yes':
        married1: ChatFullInfo = await bot.get_chat(callback_data.married1)
        married2: ChatFullInfo = await bot.get_chat(callback_data.married2)
        await set_married(callback_data.chat_id, married1.id, married2.id)
        await bot.send_message(married1.id,
                               f'Теперь вы в браке с {married2.first_name} @{married2.username}')
        await bot.send_message(married2.id,
                               f'Теперь вы в браке с {married1.first_name} @{married1.username}')

        await bot.send_message(callback_data.chat_id,
                               f'Теперь у нас новая пара: \n'
                               f'{married1.first_name} @{married1.username}'
                               f'и {married2.first_name} @{married2.username}')
        await call.answer("Ура!")
    else:
        await call.answer("Вы отказались")
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=None)


@router.message(Command("marry"))
async def marry(message: Message, bot: Bot):
    if message.reply_to_message:
        married1 = message.from_user
        married2 = message.reply_to_message.from_user
        if married1.id == married2.id:
            await message.answer("Нельзя заключить брак с самим собой")
            return
        if await get_married(married1.id) or await get_married(married2.id):
            await message.answer("Один из участников уже состоит в браке")
            return
        await message.answer(
            f"{married1.first_name} @{married1.username} "
            f"предложил заключить брак "
            f"{married2.first_name} @{married2.username}")

        button1 = InlineKeyboardButton(
            text="Да!",
            callback_data=MarriedCallback(choice="yes", married1=married1.id, married2=married2.id,
                                          chat_id=message.chat.id).pack()
        )
        button2 = InlineKeyboardButton(
            text="Нет!",
            callback_data=MarriedCallback(choice="no", married1=married1.id, married2=married2.id,
                                          chat_id=message.chat.id).pack()
        )
        kboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
        try:
            await bot.send_message(married2.id,
                                   f'{married1.first_name} @{married1.username} предложил вам заключить брак\n'
                                   f'Вы согласны?',
                                   reply_markup=kboard)
        except TelegramAPIError:
            await message.answer(f"Я не могу написать {married2.first_name} @{married2.username}\n"
                                 f"Нужно начать диалог с ботом")


@router.message(Command("divorce"))
async def divorce(message: Message):
    if await delete_married(message.from_user.id):
        await message.answer("Вы развелись со своим партнером")
    else:
        await message.answer("Вы не состоите в браке")


@router.message(Command("getmarried"))
async def get_married_users(message: Message, bot: Bot):
    married: list[Married] = await get_married_in_chat(message.chat.id)
    text = 'Браки, заключенные в этом чате: \n'
    for pair in married:
        m1: ChatFullInfo = await bot.get_chat(pair.married1)
        m2: ChatFullInfo = await bot.get_chat(pair.married2)
        text += f"{m1.first_name} @{m1.username} и {m2.first_name} @{m2.username}\n"
    await message.answer(text)
