from __future__ import annotations

from typing import TYPE_CHECKING, Any, Coroutine, ParamSpec, TypeAlias, TypeVar

if TYPE_CHECKING:
    import discord

    from .misc_command import MiscCommandContextFilled, MiscCommandContextRaw
    from .special_cog import SpecialCog

UnresolvedContext: TypeAlias = MiscCommandContextRaw | MiscCommandContextFilled | discord.Message
UnresolvedContextT = TypeVar("UnresolvedContextT", bound=UnresolvedContext)

P = ParamSpec("P")
T = TypeVar("T")

CogT = TypeVar("CogT", bound="SpecialCog[Any]")


Snowflake = int

CoroT = Coroutine[Any, Any, T]
