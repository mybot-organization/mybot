from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Coroutine

from typing_extensions import ParamSpec, TypeVar

if TYPE_CHECKING:
    import discord

    from .misc_command import MiscCommandContextFilled, MiscCommandContextRaw
    from .special_cog import SpecialCog

    MiscCommandUnresolvedContext = MiscCommandContextRaw | MiscCommandContextFilled | discord.Message


P = ParamSpec("P", default=...)
T = TypeVar("T", default=Any)
ContextT = TypeVar("ContextT", bound="MiscCommandUnresolvedContext", default=Any)

CogT = TypeVar("CogT", bound="SpecialCog[Any]")


Snowflake = int


CoroT = Coroutine[Any, Any, T]
MiscCommandCallback = Callable[Concatenate[CogT, ContextT, P], CoroT[T]]
