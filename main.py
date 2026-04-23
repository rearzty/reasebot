import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from handlers import router
from database import create_db
from middlewares.mute_check import MuteMiddleware
from middlewares.mafia_game_check import MafiaGameCheckMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage(),
                    fsm_strategy=FSMStrategy.CHAT)
    dp.include_router(router)
    dp.message.middleware(MuteMiddleware())
    dp.callback_query.middleware(MafiaGameCheckMiddleware())
    await create_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
