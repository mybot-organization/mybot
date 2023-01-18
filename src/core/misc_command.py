from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Concatenate, Coroutine, Generic, Literal

from discord import Message
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import maybe_coroutine
from typing_extensions import ParamSpec, TypeVar

from ._types import ContextT, MiscCommandContextFilled, MiscCommandContextRaw
from .errors import CheckFail, MiscCommandException, NoPrivateMessage

if TYPE_CHECKING:
    from discord import Client, Guild, Member, User
    from discord.ext.commands.bot import AutoShardedBot, Bot  # pyright: ignore[reportMissingTypeStubs]

    from ._types import ContextT, CoroT, MiscCommandCallback, MiscCommandUnresolvedContext
    from .special_cog import SpecialCog


T = TypeVar("T", default=Any)
P = ParamSpec("P", default=...)
CogT = TypeVar("CogT", bound="SpecialCog[Any]")
Coro = Coroutine[Any, Any, T]
MiscCommandParams = Concatenate[CogT, ContextT, P]

LiteralNames = Literal["raw_reaction_add"]


class MiscCommandsType(Enum):
    REACTION = "reaction"
    MESSAGE = "message"


events_to_type: dict[str, MiscCommandsType] = {
    "on_raw_reaction_add": MiscCommandsType.REACTION,
    "on_message": MiscCommandsType.MESSAGE,
}


class MiscCommand(Generic[ContextT, P, T]):
    bot: Bot | AutoShardedBot  # should be defined...

    def __init__(
        self,
        name: str,
        callback: MiscCommandCallback[Any, ContextT, P, T],
        description: str,
        nsfw: bool,
        type: MiscCommandsType,
        extras: dict[Any, Any],
    ) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.nsfw = nsfw

        self.guild_only = getattr(callback, "__misc_commands_guild_only__", False)
        self.default_permissions = 0  # TODO

        self.extras = extras

        self.checks: list[Callable[[MiscCommandContext], CoroT[bool] | bool]] = getattr(
            callback, "__misc_commands_checks__", []
        )
        self._callback: MiscCommandCallback[Any, ContextT, P, T] = callback

    async def do_call(self, cog: SpecialCog[Any], context: ContextT, *args: P.args, **kwargs: P.kwargs) -> T:
        try:
            for checker in self.checks:
                if not await maybe_coroutine(checker, await MiscCommandContext.resolve(self.bot, context)):
                    raise CheckFail()
        except MiscCommandException as e:
            self.bot.dispatch("misc_command_error", self, e, context)
            raise e

        return await self._callback(cog, context, *args, **kwargs)


def misc_command(
    name: str,
    *,
    description: str = "...",
    nsfw: bool = False,
    listener_name: LiteralNames | None = None,
    extras: dict[Any, Any] | None = None,
) -> Callable[[MiscCommandCallback[CogT, ContextT, P, T]], MiscCommandCallback[CogT, ContextT, P, T]]:
    """Register an event listener as a "command" that can be retrieved from the feature exporter.
    Checkers will be called within the second argument of the function (right after the Cog (self))

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

    def inner(func: MiscCommandCallback[CogT, ContextT, P, T]) -> MiscCommandCallback[CogT, ContextT, P, T]:
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
        async def inner(cog: CogT, context: ContextT, *args: P.args, **kwargs: P.kwargs) -> T:
            return await misc_command.do_call(cog, context, *args, **kwargs)

        setattr(inner, "__listener_as_command__", misc_command)

        add_listener = Cog.listener() if listener_name is None else Cog.listener(listener_name)
        add_listener(inner)

        return inner

    return inner


class MiscCommandContext:
    def __init__(self, guild: Guild | None, user: User | Member) -> None:
        self.guild: Guild | None = guild
        self.user: User | Member = user

    @classmethod
    async def resolve(cls, client: Client, context: MiscCommandUnresolvedContext) -> MiscCommandContext:
        guild: Guild | None
        user: User | Member

        match context:
            case Message():
                guild = context.guild
                user = context.author
            case MiscCommandContextFilled():
                guild = context.guild
                user = context.user
            case MiscCommandContextRaw():
                guild = (
                    (client.get_guild(context.guild_id) or await client.fetch_guild(context.guild_id))
                    if context.guild_id is not None
                    else None
                )
                user = client.get_user(context.user_id) or await client.fetch_user(context.user_id)

        return cls(guild, user)


def misc_guild_only() -> Callable[[T], T]:
    def predicate(ctx: MiscCommandContext) -> bool:
        if ctx.guild is None:
            raise NoPrivateMessage()
        return True

    def decorator(func: T) -> T:
        if isinstance(func, MiscCommand):
            func.guild_only = True
            func.checks.append(predicate)
        else:
            if not hasattr(func, "__misc_commands_checks__"):
                setattr(func, "__misc_commands_checks__", [])
            getattr(func, "__misc_commands_checks__").append(predicate)

            setattr(func, "__misc_commands_guild_only__", True)

        return func

    return decorator
