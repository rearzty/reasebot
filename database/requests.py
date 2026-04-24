from sqlalchemy import select
from .models import Muted, Players, Married
from . import session_maker
from sqlalchemy import or_


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


async def get_married(user_id: int) -> Married:
    async with session_maker() as session:
        married = await session.execute(
            select(Married).where(or_(Married.married1 == user_id, Married.married2 == user_id)))
        married = married.scalar()
        return married


async def get_married_in_chat(chat_id: int) -> list[Married]:
    async with session_maker() as session:
        married = await session.execute(
            select(Married).where(Married.chat_id == chat_id))
        married = married.scalars().all()
        return married


async def delete_married(user_id: int) -> bool:
    async with session_maker() as session:
        married = await session.execute(
            select(Married).where(or_(Married.married1 == user_id, Married.married2 == user_id))
        )
        married = married.scalar()
        if married:
            await session.delete(married)
            await session.commit()
            return True
        return False


async def set_married(chat_id: int, married1: int, married2: int):
    async with session_maker() as session:
        session.add(Married(chat_id=chat_id, married1=married1, married2=married2))
        await session.commit()
