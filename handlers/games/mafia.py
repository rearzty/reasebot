import asyncio
import logging
from asyncio import Lock
import random
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import User, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from aiogram.exceptions import TelegramAPIError
from enum import Enum

router = Router()
mafia_games = {}


class GameConfig:
    MIN_PLAYERS: int = 6
    WAIT_TIME: int = 10
    NIGHT_TIME: int = 30
    DAY_TIME: int = 30
    VOTING_TIME: int = 30


class Phase(Enum):
    WAITING = "waiting"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"


class Role(Enum):
    MAFIA = 'Мафия'
    DOCTOR = 'Доктор'
    CIVILIAN = 'Мирный'
    COMMISSIONER = 'Комиссар'


class Game:
    def __init__(self):
        self.phase = Phase.WAITING
        self.players: list[int] = []
        self.dead: list[int] = []
        self.killed_this_night: list[int] = []
        self.players_roles: dict[int, Role] = {}
        self.players_info: dict[int, User] = {}
        self.mafias: list[int] = []
        self.mafia_votes: dict[int, int] = {}
        self.voting: dict[int, int] = {}
        self.revived: int | None = None
        self.COMMISSIONER_kill_used: bool = False
        self.DOCTOR_self_heal_used: bool = False
        self.messages_to_be_removed: list[dict] = []
        self.action_used: dict[int, bool] = {}
        self.lock: Lock = asyncio.Lock()

    def start_game(self) -> bool:
        players = self.players
        playing = len(players)
        if playing < GameConfig.MIN_PLAYERS:
            return False
        current_roles = roles[:playing:]
        random.shuffle(current_roles)
        players_roles = self.players_roles
        for i in range(playing):
            players_roles[players[i]] = current_roles[i]
            if current_roles[i] == Role.MAFIA:
                self.mafias.append(players[i])
        return True

    def player_join(self, player: User):
        self.players_info[player.id] = player
        self.players.append(player.id)

    def player_leave(self, player: User):
        if player.id not in self.players:
            return
        del self.players_info[player.id]
        self.players.remove(player.id)

    def heal_player(self, player: User, doctor: User):
        if player.id == doctor.id:
            self.DOCTOR_self_heal_used = True
        self.revived = player.id

    def commissioner_kill(self, player: User):
        if player.id not in self.killed_this_night:
            self.killed_this_night.append(player.id)
        self.COMMISSIONER_kill_used = True

    def mafia_kill(self, player: User):
        if player.id not in self.mafia_votes:
            self.mafia_votes[player.id] = 0
        self.mafia_votes[player.id] += 1

    def end_night(self):
        if self.mafia_votes:
            mafia_results = {}
            for choice in self.mafia_votes:
                if self.mafia_votes[choice] not in mafia_results:
                    mafia_results[self.mafia_votes[choice]] = []
                mafia_results[self.mafia_votes[choice]].append(choice)
            if len(mafia_results[max(mafia_results.keys())]) > 1:
                target = random.choice(mafia_results[max(mafia_results.keys())])
            else:
                target = mafia_results[max(mafia_results.keys())][0]
            if target not in self.killed_this_night:
                self.killed_this_night.append(target)

    def get_revived(self) -> User | None:
        if self.revived and self.revived in self.killed_this_night:
            revived: User | None = self.players_info[self.revived]
            self.killed_this_night.remove(revived.id)
            return revived
        return None

    def get_killed(self) -> list[User]:
        killed: list[User] = []
        for killed_id in self.killed_this_night:
            killed_user = self.players_info[killed_id]
            killed.append(killed_user)
            self.dead.append(killed_user.id)
        return killed

    def clean_actions(self):
        self.messages_to_be_removed = []
        self.revived = None
        self.killed_this_night = []
        self.mafia_votes = {}
        self.action_used = {}
        self.voting = {}

    def get_voting_results(self) -> tuple[User, bool]:
        results = {}
        max_votes = 0
        max_votes_user_id = None
        for vote in self.voting:
            if not results.get(self.voting[vote]):
                results[self.voting[vote]] = 0
            results[self.voting[vote]] += 1
            if results[self.voting[vote]] > max_votes:
                max_votes = results[self.voting[vote]]
                max_votes_user_id = self.voting[vote]
        is_unique_winner = list(results.values()).count(max_votes) == 1
        max_votes_user = self.players_info.get(max_votes_user_id)
        if is_unique_winner and max_votes_user:
            self.dead.append(max_votes_user_id)
        return max_votes_user, is_unique_winner

    async def check_winner(self) -> tuple[bool, list[User]]:
        mafias_alive = []
        alive = []
        for player_id in self.players:
            player = self.players_info[player_id]
            if player.id not in self.dead:
                alive.append(player.id)
                if self.players_roles[player.id] == Role.MAFIA:
                    mafias_alive.append(player.id)
        if len(mafias_alive) * 2 >= len(alive):
            mafias_players: list[User] = [self.players_info[player_id] for player_id in mafias_alive]
            return True, mafias_players
        elif len(mafias_alive) == 0:
            alive_players: list[User] = [self.players_info[player_id] for player_id in alive]
            return False, alive_players
        return False, []


roles = [Role.MAFIA, Role.DOCTOR, Role.COMMISSIONER,
         Role.CIVILIAN, Role.CIVILIAN, Role.CIVILIAN,
         Role.MAFIA, Role.CIVILIAN, Role.MAFIA, Role.CIVILIAN]


class MafiaCallbackJoin(CallbackData, prefix="mafiajoin"):
    choice: str


class MafiaCallbackNight(CallbackData, prefix="mafianight"):
    action: str
    chat_id: int
    target: int


class MafiaCallbackVoting(CallbackData, prefix="mafiavoting"):
    target: int


async def finish_game_if_winner(game: Game, chat_id: int, bot: Bot) -> bool:
    mafia_won, winners = await game.check_winner()
    if not winners:
        return False

    if mafia_won:
        winners_list = ', '.join([f'{p.first_name} @{p.username}' for p in winners])
        text = f"🖤 Мафия победила!\nПобедители: {winners_list}"
    else:
        winners_list = ', '.join([f'{p.first_name} @{p.username}' for p in winners])
        text = f"🤍 Мирные победили!\nПобедители: {winners_list}"

    await send_message(bot, chat_id, text)
    del mafia_games[chat_id]
    return True


async def send_message(bot: Bot, chat_id: id, text: str,
                       reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None) -> int | Message:
    try:
        msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        return msg
    except TelegramAPIError:
        logging.warning(f'Не получилось отправить сообщение')
        return 0


async def create_users_keyboard(users_ids: list, chat_id: int, action: str) -> InlineKeyboardMarkup:
    game: Game = mafia_games[chat_id]
    buttons: list[InlineKeyboardButton] = []
    for user_id in users_ids:
        user = game.players_info[user_id]
        if user.id not in game.dead:
            button = InlineKeyboardButton(
                text=f"{user.first_name} @{user.username}",
                callback_data=MafiaCallbackNight(action=action, target=user.id, chat_id=chat_id).pack()
            )
            buttons.append(button)
    kboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return kboard


async def change_waiting_list(message: Message, game, bot: Bot):
    button1 = InlineKeyboardButton(
        text='👤 Присоединиться',
        callback_data=MafiaCallbackJoin(choice='join').pack()
    )
    button2 = InlineKeyboardButton(
        text='🚪 Выйти',
        callback_data=MafiaCallbackJoin(choice='leave').pack()
    )
    kboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
    message_text = "⌛️Ожидание игроков\n" \
                   "Подключились:\n"
    message_text += "\n".join([f"🔵 {player.first_name} @{player.username}" for player in game.players_info.values()])
    await bot.edit_message_text(text=message_text,
                                chat_id=message.chat.id, message_id=message.message_id, reply_markup=kboard)


@router.callback_query(MafiaCallbackJoin.filter())
async def join_callback(call: CallbackQuery, callback_data: MafiaCallbackJoin, bot: Bot):
    game: Game = mafia_games[call.message.chat.id]
    async with game.lock:
        player = call.from_user
        if callback_data.choice == 'join' and player.id not in game.players:
            game.player_join(player)
            await change_waiting_list(call.message, game, bot)
        elif callback_data.choice == 'leave' and player.id in game.players:
            game.player_leave(player)
            await change_waiting_list(call.message, game, bot)
        await call.answer()


@router.callback_query(MafiaCallbackNight.filter())
async def night_callback(call: CallbackQuery, callback_data: MafiaCallbackNight, bot: Bot):
    game: Game = mafia_games[callback_data.chat_id]
    async with game.lock:
        if callback_data.action == 'heal':
            target = game.players_info[callback_data.target]
            game.heal_player(target, doctor=call.from_user)
            await call.answer(f"💉 Вы решили вылечить {target.first_name} @{target.username}")
            await bot.edit_message_text(text=f"💉 Вы решили вылечить {target.first_name} @{target.username}",
                                        chat_id=call.message.chat.id, message_id=call.message.message_id)
        elif callback_data.action == 'check':
            if callback_data.target == -1:
                can_be_checked: list = game.players.copy()
                can_be_checked.remove(call.from_user.id)
                kboard = await create_users_keyboard(can_be_checked, callback_data.chat_id, 'check')
                await bot.edit_message_text(text=f"🔍 Вы решили проверить",
                                            chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = await send_message(bot, call.from_user.id, "🔍 Кого вы хотите проверить?", reply_markup=kboard)
                if msg:
                    game.messages_to_be_removed.append(
                        {'text': msg.text, 'msg_id': msg.message_id, 'chat_id': msg.chat.id})
            else:
                target = game.players_info[callback_data.target]
                await call.answer(f"🔍 Вы решили проверить {target.first_name} @{target.username}")
                await bot.edit_message_text(text=f"🔍 Вы решили проверить {target.first_name} @{target.username}",
                                            chat_id=call.message.chat.id, message_id=call.message.message_id)
                await send_message(bot, call.from_user.id,
                                   f"{target.first_name} @{target.username} - {game.players_roles[target.id]}")
        elif callback_data.action == 'kill_sheriff':
            if callback_data.target == -1:
                can_be_killed: list = game.players.copy()
                can_be_killed.remove(call.from_user.id)
                kboard = await create_users_keyboard(can_be_killed, callback_data.chat_id, 'kill_sheriff')
                await bot.edit_message_text(text=f"🩸 Вы решили убить",
                                            chat_id=call.message.chat.id, message_id=call.message.message_id)
                msg = await send_message(bot, call.from_user.id, "🩸 Кого вы хотите убить?🪦", reply_markup=kboard)
                if msg:
                    game.messages_to_be_removed.append(
                        {'text': msg.text, 'msg_id': msg.message_id, 'chat_id': msg.chat.id})
            else:
                target = game.players_info[callback_data.target]
                game.commissioner_kill(target)
                await call.answer(f"🩸 Вы решили убить {target.first_name} @{target.username}")
                await bot.edit_message_text(text=f"🩸 Вы решили убить {target.first_name} @{target.username}",
                                            chat_id=call.message.chat.id, message_id=call.message.message_id)
        elif callback_data.action == 'kill_mafia':
            target = game.players_info[callback_data.target]
            await call.answer(f"🩸 Вы решили убить {target.first_name} @{target.username}")
            await bot.edit_message_text(text=f"🩸 Вы решили убить {target.first_name} @{target.username}",
                                        chat_id=call.message.chat.id, message_id=call.message.message_id)
            game.mafia_kill(target)


@router.callback_query(MafiaCallbackVoting.filter())
async def voting_callback(call: CallbackQuery, callback_data: MafiaCallbackVoting, bot: Bot):
    game = mafia_games[call.message.chat.id]
    if game.phase != Phase.VOTING:
        await call.answer("Голосование завершено", show_alert=True)
        return
    async with game.lock:
        target = game.players_info[callback_data.target]
        caller = call.from_user
        if caller.id in game.players and game.voting.get(caller.id) != target.id and caller.id not in game.dead:
            if caller.id == target.id:
                await call.answer(f"❌ Нельзя голосовать против себя ❌")
                return
            game.voting[caller.id] = target.id
            buttons: list[list[InlineKeyboardButton]] = []
            for player_id in game.players:
                player = game.players_info[player_id]
                voted_for = list(game.voting.values()).count(player.id)
                button = InlineKeyboardButton(
                    text=f"{player.first_name} @{player.username} {voted_for}✋",
                    callback_data=MafiaCallbackVoting(target=player.id).pack()
                )
                buttons.append([button])
            kboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await bot.edit_message_text(text="🚷 Кого вы хотите выгнать?",
                                        chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=kboard)


@router.message(Command('startmafia'))
async def start_mafia(message: Message, bot: Bot):
    if not mafia_games.get(message.chat.id):
        mafia_games[message.chat.id]: Game = Game()
        asyncio.create_task(wait_for_players(message, bot))


async def wait_for_players(message: Message, bot: Bot):
    button1 = InlineKeyboardButton(
        text='👤 Присоединиться',
        callback_data=MafiaCallbackJoin(choice='join').pack()
    )
    button2 = InlineKeyboardButton(
        text='🚪 Выйти',
        callback_data=MafiaCallbackJoin(choice='leave').pack()
    )
    kboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])
    waiting_message = await message.answer("⌛️Ожидание игроков\n"
                                           "Подключились:\n", reply_markup=kboard)
    await asyncio.sleep(GameConfig.WAIT_TIME)
    game: Game = mafia_games[message.chat.id]
    game_started = game.start_game()
    if game_started:
        await message.answer("✅ Игра запущена!")
        message_text = "Игроки:\n"
        message_text += "\n".join(
            [f"🔵 {player.first_name} @{player.username}" for player in game.players_info.values()])
        await bot.edit_message_text(text=message_text,
                                    chat_id=waiting_message.chat.id, message_id=waiting_message.message_id)
        for player in game.players_roles:
            await send_message(bot, player, f"Вы {game.players_roles[player].value}")
        mafias_players: list[User] = [game.players_info[player_id] for player_id in game.mafias]
        for mafia in game.mafias:
            text = f"👥 Мафия: \n" \
                   f"{', '.join([f'{player.first_name} @{player.username}' for player in mafias_players])}"
            await send_message(bot, mafia, text)
        asyncio.create_task(night(message, bot))
    else:
        await message.answer('🚫 Недостаточно игроков\n'
                             'Отмена игры')
        await bot.delete_message(waiting_message.chat.id, waiting_message.message_id)


async def night(message: Message, bot: Bot):
    await message.answer(f'🌃 Наступает ночь! ({GameConfig.NIGHT_TIME} секунд)\n'
                         f'Город засыпает...')
    game: Game = mafia_games[message.chat.id]
    game.phase = Phase.NIGHT
    for player_id in game.players:
        if player_id in game.dead:
            continue
        player_role = game.players_roles[player_id]
        if player_role == Role.CIVILIAN:
            await send_message(bot, player_id, "Вы спите")
        elif player_role == Role.DOCTOR:
            can_be_healed: list = game.players.copy()
            if game.DOCTOR_self_heal_used:
                can_be_healed.remove(player_id)
            kboard = await create_users_keyboard(can_be_healed, message.chat.id, 'heal')
            msg = await send_message(bot, player_id, "💉 Кого вы хотите спасти? (себя можно спасти только 1 раз)",
                                     reply_markup=kboard)
            if msg:
                game.messages_to_be_removed.append(
                    {'text': msg.text, 'msg_id': msg.message_id, 'chat_id': msg.chat.id})
        elif player_role == Role.COMMISSIONER:
            buttons: list[InlineKeyboardButton] = []
            button1 = InlineKeyboardButton(
                text=f"🔍 Проверить",
                callback_data=MafiaCallbackNight(action="check", target=-1, chat_id=message.chat.id).pack()
            )
            buttons.append(button1)
            if not game.COMMISSIONER_kill_used:
                button2 = InlineKeyboardButton(
                    text=f"🩸 Убить",
                    callback_data=MafiaCallbackNight(action="kill_sheriff", target=-1, chat_id=message.chat.id).pack()
                )
                buttons.append(button2)
            kboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            msg = await send_message(bot, player_id, "Что вы хотите сделать? (убить можно только 1 раз)",
                                     reply_markup=kboard)
            if msg:
                game.messages_to_be_removed.append(
                    {'text': msg.text, 'msg_id': msg.message_id, 'chat_id': msg.chat.id})
        elif player_role == Role.MAFIA:
            can_be_killed: list = game.players.copy()
            can_be_killed.remove(player_id)
            kboard = await create_users_keyboard(can_be_killed, message.chat.id, 'kill_mafia')
            msg = await send_message(bot, player_id, "🩸 Кого вы хотите убить?🪦", reply_markup=kboard)
            if msg:
                game.messages_to_be_removed.append(
                    {'text': msg.text, 'msg_id': msg.message_id, 'chat_id': msg.chat.id})
    await asyncio.sleep(GameConfig.NIGHT_TIME)
    game.end_night()
    revived = game.get_revived()
    if revived:
        await message.answer(f"🏥 Этой ночью доктор спас {revived.first_name} @{revived.username}")
    killed = game.get_killed()
    for user in killed:
        await message.answer(f"🪦 Этой ночью умер {user.first_name} @{user.username}")
    for msg in game.messages_to_be_removed:
        await bot.edit_message_text(text=msg['text'],
                                    chat_id=msg['chat_id'], message_id=msg['msg_id'])

    game.clean_actions()
    if await finish_game_if_winner(game, message.chat.id, bot):
        return
    asyncio.create_task(day(message, bot))


async def day(message: Message, bot: Bot):
    game: Game = mafia_games[message.chat.id]
    await message.answer(f'🌅 Наступает день! ({GameConfig.DAY_TIME} секунд)\n'
                         f'Город просыпается...')
    game.phase = Phase.DAY
    await asyncio.sleep(GameConfig.DAY_TIME)
    asyncio.create_task(voting(message, bot))


async def voting(message: Message, bot: Bot):
    game: Game = mafia_games[message.chat.id]
    await message.answer(f'📌 Пришло время голосовать! ({GameConfig.VOTING_TIME} секунд)')
    game.phase = Phase.VOTING
    buttons: list[list[InlineKeyboardButton]] = []
    for player_id in game.players:
        player = game.players_info[player_id]
        if player.id not in game.dead:
            button = InlineKeyboardButton(
                text=f"{player.first_name} @{player.username} 0✋",
                callback_data=MafiaCallbackVoting(target=player.id).pack()
            )
            buttons.append([button])
    kboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    voting_message = await send_message(bot, message.chat.id, "🚷 Кого вы хотите выгнать?", reply_markup=kboard)
    await asyncio.sleep(GameConfig.VOTING_TIME)
    await bot.edit_message_text(text="Голосование завершено",
                                chat_id=voting_message.chat.id, message_id=voting_message.message_id)
    max_votes_user, is_unique_winner = game.get_voting_results()

    if is_unique_winner and max_votes_user:
        await message.answer(f"🚷 Город решил выгнать {max_votes_user.first_name} @{max_votes_user.username}")
    else:
        await message.answer("Никого не выгнали")

    if await finish_game_if_winner(game, message.chat.id, bot):
        return
    game.clean_actions()
    asyncio.create_task(night(message, bot))
