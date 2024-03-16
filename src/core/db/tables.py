from __future__ import annotations

import enum
from collections.abc import Iterable, Sequence
from datetime import datetime
from functools import partial
from typing import Annotated, Any, ClassVar, TypeVar

from sqlalchemy import ARRAY, BigInteger, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, INTEGER, JSONB, SMALLINT, VARCHAR
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column as _mapped_column, relationship
from sqlalchemy.sql import functions

T = TypeVar("T")

mapped_column = partial(_mapped_column, default=None)

Snowflake = Annotated[int, mapped_column(BIGINT)]
TimestampFK = Annotated[datetime, mapped_column(server_default=functions.now(), primary_key=True)]


class MutableList(Mutable, list[T]):
    def append(self, value: T):
        list[T].append(self, value)
        self.changed()

    def remove(self, value: T):
        list[T].remove(self, value)
        self.changed()

    def clear(self):
        list[T].clear(self)
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


class Base(MappedAsDataclass, AsyncAttrs, DeclarativeBase):
    type_annotation_map: ClassVar = {
        bool: BOOLEAN,
        int: INTEGER,
    }


class GuildDB(Base):
    __tablename__ = "guild"

    guild_id: Mapped[Snowflake] = mapped_column(primary_key=True)
    premium_type: Mapped[PremiumType] = mapped_column(Enum(PremiumType), default=PremiumType.NONE)
    translations_are_public: Mapped[bool] = mapped_column(default=False)


class UserDB(Base):
    __tablename__ = "user"

    user_id: Mapped[Snowflake] = mapped_column(primary_key=True)


class Poll(Base, kw_only=True):
    __tablename__ = "poll"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[Snowflake] = mapped_column()
    channel_id: Mapped[Snowflake] = mapped_column()
    guild_id: Mapped[Snowflake] = mapped_column(ForeignKey(GuildDB.guild_id))
    author_id: Mapped[Snowflake] = mapped_column()
    type: Mapped[PollType] = mapped_column(Enum(PollType))
    title: Mapped[str] = mapped_column(VARCHAR)  # todo: define max length
    description: Mapped[str | None] = mapped_column(VARCHAR)  # todo: define max length
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_answers: Mapped[int] = mapped_column(SMALLINT, default=1)
    users_can_change_answer: Mapped[bool] = mapped_column(default=True)
    public_results: Mapped[bool] = mapped_column(default=True)
    closed: Mapped[bool] = mapped_column(default=False)
    anonymous_allowed: Mapped[bool] = mapped_column(default=False)
    allowed_roles: Mapped[list[Snowflake]] = _mapped_column(
        MutableList.as_mutable(ARRAY(BigInteger)), default_factory=list
    )

    choices: Mapped[list[PollChoice]] = relationship(cascade="all, delete-orphan", default_factory=list)


class PollChoice(Base):
    __tablename__ = "poll_choice"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey(Poll.id))
    label: Mapped[str] = mapped_column(VARCHAR)  # todo: define max length


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
    value: Mapped[str] = mapped_column(VARCHAR)  # use JSONB instead?
    user_id: Mapped[Snowflake] = mapped_column()
    anonymous: Mapped[bool] = mapped_column(default=False)


class TSGuildCount(Base):
    __tablename__ = "ts_guild_count"

    ts: Mapped[TimestampFK] = mapped_column()
    value: Mapped[int] = mapped_column()


class TSUsage(Base):
    __tablename__ = "ts_command_usage"

    ts: Mapped[TimestampFK] = mapped_column()
    user_id: Mapped[Snowflake] = mapped_column()  # ForeignKey(UserDB.user_id))
    guild_id: Mapped[Snowflake | None] = mapped_column(ForeignKey(GuildDB.guild_id))
    data: Mapped[dict[str, Any]] = _mapped_column(JSONB, default_factory=dict)


class TSPollModification(Base):
    __tablename__ = "ts_poll_modification"

    ts: Mapped[TimestampFK] = mapped_column()
    user_id: Mapped[Snowflake] = mapped_column()
    poll_id: Mapped[int] = mapped_column(ForeignKey(Poll.id))
    data: Mapped[dict[str, Any]] = _mapped_column(JSONB, default_factory=dict)


class TSSettingUpdate(Base):
    __tablename__ = "ts_setting_update"

    ts: Mapped[TimestampFK] = mapped_column()
    guild_id: Mapped[Snowflake] = mapped_column(ForeignKey(GuildDB.guild_id))
    user_id: Mapped[Snowflake] = mapped_column()
    data: Mapped[dict[str, Any]] = _mapped_column(JSONB, default_factory=dict)
