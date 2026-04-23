from sqlalchemy import select
from .models import Muted, Players
from . import session_maker
from sqlalchemy.exc import IntegrityError


async def is_muted(chat_id: int, user_id: int) -> bool:
    async with session_maker() as session:
        result = await session.execute(
            select(Muted).where(Muted.chat_id == chat_id, Muted.user_id == user_id)
        )
        return result.scalar()


async def add_muted(chat_id: int, user_id: int) -> None:
    async with session_maker() as session:
        session.add(Muted(chat_id=chat_id, user_id=user_id))
        await session.commit()


async def remove_muted(chat_id: int, user_id: int) -> None:
    async with session_maker() as session:
        muted = await session.execute(
            select(Muted).where(Muted.chat_id == chat_id, Muted.user_id == user_id)
        )
        muted = muted.scalar()
        if muted:
            await session.delete(muted)
            await session.commit()


async def get_muted(chat_id: int) -> list[Muted]:
    async with session_maker() as session:
        muted = await session.execute(
            select(Muted).where(Muted.chat_id == chat_id)
        )
        muted = muted.scalars().all()
        return muted


async def add_player(user_id: int, score: int, username: str) -> None:
    async with session_maker() as session:
        session.add(Players(user_id=user_id, score=score, username=username))
        await session.commit()


async def get_player(user_id: int) -> list[Players]:
    async with session_maker() as session:
        player = await session.execute(
            select(Players).where(Players.user_id == user_id)
        )
        return player.scalar()


async def update_player(user_id: int, username: str) -> None:
    async with session_maker() as session:
        player = await session.execute(
            select(Players).where(Players.user_id == user_id)
        )
        player = player.scalar()

        if player:
            player.score += 1
        else:
            session.add(Players(user_id=user_id, score=1, username=username))
        await session.commit()


async def get_players() -> list[Players]:
    async with session_maker() as session:
        players = await session.execute(
            select(Players).order_by(Players.score.desc())
        )
        players = players.scalars().all()
        return players
