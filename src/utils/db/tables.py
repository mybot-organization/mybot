from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class PollType(enum.Enum):
    CHOICE = 1


class UsageType(enum.Enum):
    SLASHCOMMAND = 1


class PremiumType(enum.Enum):
    NONE = 1


class Base(DeclarativeBase):
    pass


class GuildDB(Base):
    __tablename__ = "guild"

    guild_id: Mapped[int] = mapped_column(primary_key=True)
    premium_type: Mapped[PremiumType] = mapped_column(Enum(PremiumType))
    translations_are_public: Mapped[bool] = mapped_column(Boolean)


class UserDB(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True)


class Poll(Base):
    __tablename__ = "poll"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(Integer)
    channel_id: Mapped[int] = mapped_column(Integer)
    guild_id: Mapped[GuildDB] = mapped_column(ForeignKey(GuildDB.guild_id))
    author_id: Mapped[int] = mapped_column(Integer)
    type: Mapped[PollType] = mapped_column(Enum(PollType))
    multiple: Mapped[bool] = mapped_column(Boolean)
    label: Mapped[str] = mapped_column(String)
    creation_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime | None] = mapped_column(Date)

    choices: Mapped[list[PollChoice]] = relationship()


class PollChoice(Base):
    __tablename__ = "poll_choice"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[Poll] = mapped_column(ForeignKey(Poll.id))
    label: Mapped[str] = mapped_column(String)


class PollAnswer(Base):
    __tablename__ = "poll_answer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey(Poll.id))
    value: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(Integer)


class Usage(Base):
    __tablename__ = "usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[UsageType] = mapped_column(Enum(UsageType))
    details: Mapped[str] = mapped_column(String)
    user_id: Mapped[UserDB] = mapped_column(ForeignKey(UserDB.user_id))
    guild_id: Mapped[GuildDB] = mapped_column(ForeignKey(GuildDB.guild_id))
