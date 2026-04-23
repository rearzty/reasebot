from aiogram.fsm.state import State, StatesGroup
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.requests import add_player, get_player, update_player, get_players
import random

router = Router()


class GuessGame(StatesGroup):
    playing = State()


@router.message(Command("guessnumber"))
async def start_guess(message: Message, state: FSMContext):
    await state.set_state(GuessGame.playing)
    await state.update_data(number=random.randint(1, 100))
    await message.answer("Игра началась!")


@router.message(Command("stopguess"), GuessGame.playing)
async def stop_guess(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Игра остановлена")


@router.message(Command("leaderboard"))
async def get_leaderboard(message: Message):
    players = (await get_players())[:10:]
    players = "\n".join([f"{player.username} - {player.score}" for player in players])
    await message.answer(f'--- Таблица лидеров ---\n{players}')


@router.message(GuessGame.playing)
async def process_guess(message: Message, state: FSMContext):
    if message.text.isdigit():
        if int(message.text) == (await state.get_data())['number']:
            await state.clear()
            await message.answer("Правильно!")
            await update_player(message.from_user.id, message.from_user.username)
        elif int(message.text) > (await state.get_data())['number']:
            await message.answer("Нужно меньше!")
        elif int(message.text) < (await state.get_data())['number']:
            await message.answer("Нужно больше!")
