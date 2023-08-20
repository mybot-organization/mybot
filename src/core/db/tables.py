from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Iterable, Sequence, TypedDict, TypeVar, Unpack

from sqlalchemy import ARRAY, TIMESTAMP, BigInteger, Boolean, DateTime, Enum, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import functions
from sqlalchemy.sql.schema import ColumnDefault

T = TypeVar("T")


class MutableList(Mutable, list[T]):
    def append(self, value: T):
        list[T].append(self, value)
        self.changed()

    def remove(self, value: T):
        list[T].remove(self, value)
        self.changed()

    def clear(self):
        list.clear(self)
        self.changed()

    def extend(self, value: Iterable[T]):
        list[T].extend(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key: str, value: Sequence[T]) -> MutableList[T] | Mutable | None:
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)

        return value


class PollType(enum.Enum):
    CHOICE = 1  # A poll with multiple choices
    BOOLEAN = 2  # A poll with only "yes" and "no"
    OPINION = 3  # A poll with nuanced opinions
    ENTRY = 4  # A poll where users can enter their own choices


class PremiumType(enum.Enum):
    NONE = 1


class Base(DeclarativeBase):
    pass


class GuildDB(Base):
    __tablename__ = "guild"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    premium_type: Mapped[PremiumType] = mapped_column(Enum(PremiumType))
    translations_are_public: Mapped[bool] = mapped_column(Boolean)


class UserDB(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


class PollKwargs(TypedDict, total=False):
    message_id: int
    channel_id: int
    channel_id: int
    guild_id: int
    author_id: int
    type: PollType
    title: str
    creation_date: datetime
    description: str | None
    end_date: datetime | None
    max_answers: int
    users_can_change_answers: bool
    public_results: bool
    closed: bool
    anonymous_allowed: bool
    allowed_roles: list[int]


class Poll(Base):
    __tablename__ = "poll"

    def __init__(self, **kwargs: Unpack[PollKwargs]):
        for m in self.__mapper__.columns:
            if m.name not in kwargs and m.default is not None and isinstance(m.default, ColumnDefault):
                kwargs[m.name] = m.default.arg

        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    guild_id: Mapped[int] = mapped_column(ForeignKey(GuildDB.guild_id), nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[PollType] = mapped_column(Enum(PollType), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    max_answers: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    users_can_change_answer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    public_results: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonymous_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_roles: Mapped[list[int]] = mapped_column(
        MutableList.as_mutable(ARRAY(BigInteger)), nullable=False, default=[]
    )

    choices: Mapped[list[PollChoice]] = relationship(cascade="all, delete-orphan")


class PollChoice(Base):
    __tablename__ = "poll_choice"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[Poll] = mapped_column(ForeignKey(Poll.id))
    label: Mapped[str] = mapped_column(String, nullable=False)


class PollAnswer(Base):
    """
    value is:
        - the choice id if the poll is a choice poll
        - "0" or "1" if the poll is a boolean poll
        - ...
    """

    __tablename__ = "poll_answer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey(Poll.id))
    value: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(BigInteger)
    anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TSGuildCount(Base):
    __tablename__ = "ts_guild_count"

    ts: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True, server_default=functions.now(), nullable=False)
    value: Mapped[int] = mapped_column(nullable=False)


class TSUsage(Base):
    __tablename__ = "ts_command_usage"

    ts: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True, server_default=functions.now(), nullable=False)
    user_id: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)  # ForeignKey(UserDB.user_id))
    guild: Mapped[GuildDB] = mapped_column(ForeignKey(GuildDB.guild_id), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default={}, nullable=False)


class TSPollModification(Base):
    __tablename__ = "ts_poll_modification"

    ts: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True, server_default=functions.now(), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    poll_id: Mapped[int] = mapped_column(ForeignKey(Poll.id), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default={}, nullable=False)


class TSSettingUpdate(Base):
    __tablename__ = "ts_setting_update"

    ts: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True, server_default=functions.now(), nullable=False)
    guild_id: Mapped[int] = mapped_column(ForeignKey(GuildDB.guild_id), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default={}, nullable=False)
