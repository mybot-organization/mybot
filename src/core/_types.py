from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Coroutine, Protocol, runtime_checkable

from typing_extensions import ParamSpec, TypeVar

if TYPE_CHECKING:
    import discord

    from .special_cog import SpecialCog

P = ParamSpec("P", default=...)
T = TypeVar("T", default=Any)
ContextT = TypeVar("ContextT", bound="MiscCommandUnresolvedContext", default=Any)

CogT = TypeVar("CogT", bound="SpecialCog[Any]")


@runtime_checkable
class MiscCommandContextRaw(Protocol):
    guild_id: None | int  # to work with raw events
    user_id: int


@runtime_checkable
class MiscCommandContextFilled(Protocol):
    guild: None | discord.Guild
    user: discord.User


MiscCommandUnresolvedContext = MiscCommandContextRaw | MiscCommandContextFilled | discord.Message


Snowflake = int


CoroT = Coroutine[Any, Any, T]
MiscCommandCallback = Callable[Concatenate[CogT, ContextT, P], CoroT[T]]
