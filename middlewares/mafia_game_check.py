from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, CallbackQuery
from handlers.games.mafia import mafia_games, Phase


class MafiaGameCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        if not event.callback_query or not event.callback_query.data:
            return handler(event, data)
        call: CallbackQuery = event.callback_query
        if not call.data.startswith('mafia'):
            return handler(event, data)
        chat_id = event.callback_query.message.chat.id
        is_night = event.callback_query.data.startswith('mafianight')
        if is_night:
            chat_id = int(event.callback_query.data.split(':')[2])

        game = mafia_games.get(chat_id)

        if not game:
            await call.answer("Игра не найдена")
            return
        if is_night and game.action_used.get(call.from_user.id, False):
            await call.answer("Нельзя!")
            return
        user_id = call.from_user.id

        if user_id not in game.players or user_id in game.dead:
            await call.answer("Нельзя!")
            return
        if is_night and game.phase != Phase.NIGHT:
            await call.answer("❌ Ночь уже закончилась", show_alert=True)
            return
        game.action_used[call.from_user.id] = True
        return await handler(event, data)
