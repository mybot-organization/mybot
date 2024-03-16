from __future__ import annotations

from typing import TYPE_CHECKING, Any, ParamSpec, TypeAlias, TypeVar, Union
from collections.abc import Coroutine

from discord import Message
from discord.ext import commands

if TYPE_CHECKING:
    from .extended_commands import ExtendedCog, MiscCommandContextFilled, MiscCommandContextRaw

UnresolvedContext: TypeAlias = Union["MiscCommandContextRaw", "MiscCommandContextFilled", Message]
UnresolvedContextT = TypeVar("UnresolvedContextT", bound=UnresolvedContext)

P = ParamSpec("P")
T = TypeVar("T")

CogT = TypeVar("CogT", bound="ExtendedCog")
BotT = TypeVar("BotT", bound="commands.Bot | commands.AutoShardedBot")


Snowflake = int

CoroT = Coroutine[Any, Any, T]
