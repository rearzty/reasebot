from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    pass


class Muted(Base):
    __tablename__ = "muted"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)


class Banned(Base):
    __tablename__ = "banned"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)


class Players(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False)


class Married(Base):
    __tablename__ = "married"
    id: Mapped[int] = mapped_column(primary_key=True)
    married1: Mapped[int] = mapped_column(nullable=False)
    married2: Mapped[int] = mapped_column(nullable=False)
    chat_id: Mapped[int] = mapped_column(nullable=False)


class Trigger(Base):
    __tablename__ = "triggers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(unique=True)
    responses: Mapped[list["Response"]] = relationship(back_populates="trigger")


class Response(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("triggers.id"))
    text: Mapped[str]
    weight: Mapped[int] = mapped_column(default=1)
    trigger: Mapped["Trigger"] = relationship(back_populates="responses")
