from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, Literal

from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from typing_extensions import ParamSpec, TypeVar

if TYPE_CHECKING:
    from discord.ext.commands.bot import BotBase  # pyright: ignore[reportMissingTypeStubs]


T = TypeVar("T", default=Any)
P = ParamSpec("P", default=...)
Coro = Coroutine[Any, Any, T]
MiscCommandCallback = Callable[P, Coro[T]]

LiteralNames = Literal["raw_reaction_add"]


class MiscCommandsType(Enum):
    REACTION = "reaction"
    MESSAGE = "message"


events_to_type: dict[str, MiscCommandsType] = {
    "on_raw_reaction_add": MiscCommandsType.REACTION,
    "on_message": MiscCommandsType.MESSAGE,
}


class MiscCommand(Generic[P]):
    bot: BotBase  # should be binder right after the class is created with bind_misc_commands

    def __init__(
        self,
        name: str,
        callback: MiscCommandCallback[P, T],
        description: str,
        nsfw: bool,
        type: MiscCommandsType,
        extras: dict[Any, Any],
    ) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.nsfw = nsfw

        self.guild_only = False  # TODO
        self.default_permissions = 0  # TODO

        self.extras = extras

        self.checkers: list[Callable[..., Any]] = []
        self._callback = callback

    async def do_call(self, *args: P.args, **kwargs: P.kwargs) -> Any:
        for checker in self.checkers:
            await checker(*args, **kwargs)
        return await self._callback(*args, **kwargs)


def misc_command(
    name: str,
    *,
    description: str = "...",
    nsfw: bool = False,
    listener_name: LiteralNames | None = None,
    extras: dict[Any, Any] | None = None,
) -> Callable[..., Any]:
    """Register an event listener as a "command" that can be retrieved from the feature exporter.

    Args:
        name (str): name of the "command"
        description (str, optional): Description of the command. Defaults to "...".
        guild_only (bool, optional): If feature is only on guild or not. DO NOT DO ANY CHECK. Defaults to False.
        nsfw (bool, optional): If the feature contains NSFW content. DO NOT DO ANY CHECK. Defaults to False.
        default_permissions (int | None, optional): Default permissions needed to use the feature. DO NOT DO ANY CHECK. Defaults to None.
        listener_name (LiteralNames | None, optional): If the function has a specific name, set the event name here. Defaults to None.
        extras (dict[Any, Any] | None, optional): Some extras informations. Defaults to None.

    Returns:
        Callable[..., Any]: A wrapped function, bound with a MiscCommand.
    """

    def inner(func: MiscCommandCallback[P, T]) -> MiscCommandCallback[P, T]:
        true_listener_name = listener_name or func.__name__

        misc_command = MiscCommand(
            name=name,
            callback=func,
            description=description,
            nsfw=nsfw,
            type=events_to_type[true_listener_name],
            extras=extras or {},
        )

        @wraps(func)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
            return await misc_command.do_call(*args, **kwargs)

        setattr(inner, "__listener_as_command__", misc_command)

        add_listener = Cog.listener() if listener_name is None else Cog.listener(listener_name)
        add_listener(inner)

        return inner

    return inner


# def misc_check(predicate: "Check") -> Callable[[T], T]:
#     def decorator(func: CheckInputParameter) -> CheckInputParameter:
#         func.checks.append(predicate)
#         return func

#     return decorator
