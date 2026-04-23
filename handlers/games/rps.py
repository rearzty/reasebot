from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters.callback_data import CallbackData

router = Router()
games = {}
choices = {'rock': 'камень', 'scissors': 'ножницы', 'paper': 'бумага'}


class RpsGame:
    def __init__(self, chat_message, player1, player2, message_to_player_1, message_to_player_2):
        self.chat_message = chat_message
        self.players = {
            player1.id: {'message': message_to_player_1, 'choice': None},
            player2.id: {'message': message_to_player_2, 'choice': None},
        }


class RpsCallback(CallbackData, prefix="rps"):
    choice: str
    player1: int
    player2: int


def get_winner(pair):
    game: RpsGame = games[pair]
    p1 = game.players[pair[0]]['choice']
    p2 = game.players[pair[1]]['choice']
    if (p1 == 'rock' and p2 == 'scissors') or (p1 == 'paper' and p2 == 'rock') or (p1 == 'scissors' and p2 == 'paper'):
        return pair[0]
    elif p1 == p2:
        return "Ничья"
    else:
        return pair[1]


@router.callback_query(RpsCallback.filter())
async def get_callback(call: CallbackQuery, callback_data: RpsCallback, bot: Bot):
    pair = (callback_data.player1, callback_data.player2)
    if pair in games and call.from_user.id in pair and not games[pair].players[call.from_user.id]['choice']:
        game: RpsGame = games[pair]
        game.players[call.from_user.id]['choice'] = callback_data.choice
        await bot.edit_message_text(text=call.message.text + f"\nВаш выбор: {choices[callback_data.choice]}",
                                    reply_markup=None,
                                    chat_id=call.message.chat.id, message_id=call.message.message_id)
        if game.players[pair[0]]['choice'] and game.players[pair[1]]['choice']:
            winner = get_winner(pair)
            if winner != 'Ничья':
                winner = await bot.get_chat(winner)
                winner = f"{winner.first_name} @{winner.username}"
            chat_message = game.chat_message
            await bot.edit_message_text(text=chat_message.text + f"\nПобедитель: {winner}",
                                        chat_id=chat_message.chat.id, message_id=chat_message.message_id)
            del games[pair]
    await call.answer()


@router.message(Command('rps'))
async def start_game(message: Message, bot: Bot):
    if message.reply_to_message:
        if message.from_user.id == message.reply_to_message.from_user.id or message.reply_to_message.from_user.is_bot:
            return
        player1 = message.from_user
        player2 = message.reply_to_message.from_user
        pair = tuple(sorted([player1.id, player2.id]))
        if pair in games:
            await bot.delete_message(chat_id=games[pair].chat_message.chat.id,
                                     message_id=games[pair].chat_message.message_id)
            for player in games[pair].players:
                await bot.delete_message(chat_id=player,
                                         message_id=games[pair]['players'][player]['message'].message_id)
            del games[pair]
        message_sent = await message.answer(
            f"{player1.first_name or '@' + player1.username} x {player2.first_name or '@' + player2.username}")
        button1 = InlineKeyboardButton(
            text='Камень',
            callback_data=RpsCallback(choice='rock', player1=pair[0], player2=pair[1]).pack()
        )
        button2 = InlineKeyboardButton(
            text='Ножницы',
            callback_data=RpsCallback(choice='scissors', player1=pair[0], player2=pair[1]).pack()
        )
        button3 = InlineKeyboardButton(
            text='Бумага',
            callback_data=RpsCallback(choice='paper', player1=pair[0], player2=pair[1]).pack()
        )
        kboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2, button3]])
        message_to_player_1 = await bot.send_message(player1.id,
                                                     f"Вы играете с {player2.first_name} @{player2.username}",
                                                     reply_markup=kboard)
        message_to_player_2 = await bot.send_message(player2.id,
                                                     f"Вы играете с {player1.first_name} @{player1.username}",
                                                     reply_markup=kboard)

        games[pair] = RpsGame(message_sent, player1, player2, message_to_player_1, message_to_player_2)
