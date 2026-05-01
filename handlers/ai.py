from aiogram import Router
from aiogram.types import Message
from database.requests import get_responses, add_response
import random

router = Router()


@router.message()
async def echo(message: Message):
    reply_to = message.reply_to_message
    if reply_to and reply_to.text and len(reply_to.text) > 2 and message.text and len(message.text) > 2:
        replied_to = message.reply_to_message.from_user
        if replied_to.is_bot:
            responses = await get_responses(message.text.lower())
            if responses:
                resps = [r.text for r in responses]
                ws = [r.weight for r in responses]
                text = random.choices(resps, ws)[0]
                await message.reply(text)
        else:
            await add_response(reply_to.text.lower(), message.text.lower())
