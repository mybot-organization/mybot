from __future__ import annotations

from typing import TYPE_CHECKING, Any, Coroutine, ParamSpec, TypeAlias, TypeVar, Union

from discord import Message
from discord.ext import commands

if TYPE_CHECKING:
    from .misc_command import MiscCommandContextFilled, MiscCommandContextRaw
    from .special_cog import SpecialCog

UnresolvedContext: TypeAlias = Union["MiscCommandContextRaw", "MiscCommandContextFilled", Message]
UnresolvedContextT = TypeVar("UnresolvedContextT", bound=UnresolvedContext)

P = ParamSpec("P")
T = TypeVar("T")

CogT = TypeVar("CogT", bound="SpecialCog[Any]")
BotT = TypeVar("BotT", bound="commands.Bot | commands.AutoShardedBot")


Snowflake = int

CoroT = Coroutine[Any, Any, T]
