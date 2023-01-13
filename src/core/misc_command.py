from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, TypeVar, runtime_checkable

from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from discord.ext.commands.bot import BotBase  # pyright: ignore[reportMissingTypeStubs]


Func = TypeVar("Func", bound="FuncListener")
LiteralNames = Literal["raw_reaction_add"]


class MiscCommandsType(Enum):
    REACTION = "reaction"
    MESSAGE = "message"


events_to_type: dict[str, MiscCommandsType] = {
    "on_raw_reaction_add": MiscCommandsType.REACTION,
    "on_message": MiscCommandsType.MESSAGE,
}


@runtime_checkable
class FuncListener(Protocol):
    __listener_as_command__: MiscCommand
    __name__: str

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class MiscCommand:
    bot: BotBase  # should be binder right after the class is created with bind_misc_commands

    def __init__(
        self,
        name: str,
        callback: FuncListener,
        description: str,
        guild_only: bool,
        nsfw: bool,
        default_permissions: int | None,
        type: MiscCommandsType,
        extras: dict[Any, Any],
    ) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.guild_only = guild_only
        self.nsfw = nsfw
        self.default_permissions = default_permissions

        self.extras = extras

        self.checkers: list[Callable[..., Any]] = []
        self._callback = callback

    async def _do_call(self, *args: Any, **kwds: Any) -> Any:
        for checker in self.checkers:
            await checker(*args, **kwds)
        return await self._callback(*args, **kwds)


def misc_command(
    name: str,
    description: str = "...",
    guild_only: bool = False,
    nsfw: bool = False,
    default_permissions: int | None = None,
    listener_name: LiteralNames | None = None,
    extras: dict[Any, Any] | None = None,
) -> Callable[..., Any]:
    """Register an event listener as a "command" that can be retrieved from the feature exporter.

    Args:
        name (str): name of the "command"
        description (str, optional): Descrption of the command. Defaults to "...".
        guild_only (bool, optional): If feature is only on guild or not. DO NOT DO ANY CHECK. Defaults to False.
        nsfw (bool, optional): If the feature contains NSFW content. DO NOT DO ANY CHECK. Defaults to False.
        default_permissions (int | None, optional): Default permissions needed to use thre feature. DO NOT DO ANY CHECK. Defaults to None.
        listener_name (LiteralNames | None, optional): If the function has a specific name, set the event name here. Defaults to None.
        extras (dict[Any, Any] | None, optional): Some extras informations. Defaults to None.

    Returns:
        Callable[..., Any]: A wrapped function, binded with a MiscCommand.
    """

    def inner(func: Func) -> Func:
        true_listener_name = listener_name or func.__name__

        misc_command = MiscCommand(
            name=name,
            callback=func,
            description=description,
            guild_only=guild_only,
            nsfw=nsfw,
            default_permissions=default_permissions,
            type=events_to_type[true_listener_name],
            extras=extras or {},
        )

        @wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            return await misc_command._do_call(*args, **kwargs)  # type: ignore

        setattr(inner, "__listener_as_command__", misc_command)

        add_listener = Cog.listener() if listener_name is None else Cog.listener(listener_name)
        add_listener(inner)

        return inner  # type: ignore  # TODO : maybe using args etc we can do better

    return inner
