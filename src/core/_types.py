from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Coroutine, Protocol

from typing_extensions import ParamSpec, TypeVar

if TYPE_CHECKING:
    from .special_cog import SpecialCog

P = ParamSpec("P", default=...)
T = TypeVar("T", default=Any)
ContextT = TypeVar("ContextT", bound="MiscCommandCheckerContext", default=Any)

CogT = TypeVar("CogT", bound="SpecialCog[Any]")


class MiscCommandCheckerContext(Protocol):
    guild_id: None | int  # to work with raw events
    user_id: int


Snowflake = int


CoroT = Coroutine[Any, Any, T]
MiscCommandCallback = Callable[Concatenate[CogT, ContextT, P], CoroT[T]]
