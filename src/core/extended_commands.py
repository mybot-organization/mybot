from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    Self,
    Sequence,
    TypeVar,
    cast,
    runtime_checkable,
)

import discord
from discord import ClientUser, Member, Permissions, User
from discord.ext import commands
from discord.utils import maybe_coroutine
from typing_extensions import TypeVar

from ._types import BotT, CogT
from .errors import MiscCheckFailure, MiscCommandError, MiscNoPrivateMessage, UnexpectedError

if TYPE_CHECKING:
    from discord.abc import MessageableChannel, Snowflake
    from discord.ext.commands.bot import AutoShardedBot, Bot, BotBase  # pyright: ignore[reportMissingTypeStubs]

    from mybot import MyBot

    from ._types import CoroT, UnresolvedContext, UnresolvedContextT

    ConditionCallback = Callable[Concatenate["CogT", UnresolvedContextT, "P"], CoroT[bool] | bool]
    Callback = Callable[Concatenate["CogT", UnresolvedContextT, "P"], CoroT["T"]]

P = ParamSpec("P")
T = TypeVar("T")
C = TypeVar("C", bound="commands.Cog")
_BotType = TypeVar("_BotType", bound="Bot | AutoShardedBot")


LiteralNames = Literal["raw_reaction_add", "message"]


class MiscCommandsType(Enum):
    REACTION = "reaction"
    MESSAGE = "message"


events_to_type: dict[str, MiscCommandsType] = {
    "on_raw_reaction_add": MiscCommandsType.REACTION,
    "on_message": MiscCommandsType.MESSAGE,
}


class ExtendedCog(commands.Cog):
    __cog_misc_commands__: list[MiscCommand[Any, ..., Any]]
    bot: MyBot

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        cls = super().__new__(cls, *args, **kwargs)

        cls.__cog_misc_commands__ = []
        for _, listener in cls.__cog_listeners__:
            misc_command = getattr(getattr(cls, listener), "__listener_as_command__", None)
            if isinstance(misc_command, MiscCommand):
                cls.__cog_misc_commands__.append(misc_command)  # pyright: ignore [reportUnknownArgumentType]

        return cls

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    def get_misc_commands(self) -> list[MiscCommand[Any, ..., Any]]:
        """Return all the misc commands in this cog."""
        return list(self.__cog_misc_commands__)

    async def _inject(self, bot: BotBase, override: bool, guild: Snowflake | None, guilds: Sequence[Snowflake]) -> Self:
        await super()._inject(bot, override, guild, guilds)

        # bind the bot to the misc commands
        # used to dispatch error for error handling
        for misc_command in self.get_misc_commands():
            misc_command.bot = bot  # type: ignore

        return self


class ExtendedGroupCog(ExtendedCog):
    __cog_is_app_commands_group__: ClassVar[bool] = True


class MiscCommand(Generic[CogT, P, T]):
    bot: Bot | AutoShardedBot

    def __init__(
        self,
        name: str,
        callback: Callback[CogT, UnresolvedContextT, P, T],
        description: str,
        nsfw: bool,
        type: MiscCommandsType,
        extras: dict[Any, Any],
        trigger_condition: Callable[Concatenate[CogT, UnresolvedContext, P], bool | CoroT[bool]] | None,
    ) -> None:
        self.name = name
        self.type = type
        self.description = description
        self.nsfw = nsfw

        self.guild_only = getattr(callback, "__misc_commands_guild_only__", False)
        self.default_permissions = 0  # TODO(airo.pi_)

        self.extras = extras | getattr(callback, "__misc_commands_extras__", {})

        self.trigger_condition = trigger_condition

        self.checks: list[Callable[[MiscCommandContext[Any]], CoroT[bool] | bool]] = getattr(
            callback, "__misc_commands_checks__", []
        )
        self._callback = callback

    async def do_call(self, cog: CogT, context: UnresolvedContext, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.trigger_condition:
            trigger_condition = await discord.utils.maybe_coroutine(
                self.trigger_condition, cog, context, *args, **kwargs  # type: ignore
            )
            if not trigger_condition:
                return  # type: ignore
        resolved_context = await MiscCommandContext.resolve(self.bot, context, self)
        try:
            for checker in self.checks:
                if not await maybe_coroutine(checker, resolved_context):
                    raise MiscCheckFailure()
        except MiscCommandError as e:
            self.bot.dispatch("misc_command_error", resolved_context, e)
            return  # type: ignore

        return await self._callback(cog, context, *args, **kwargs)  # type: ignore

    def add_check(self, predicate: Callable[[MiscCommandContext[Any]], CoroT[bool] | bool]) -> None:
        self.checks.append(predicate)

    async def condition(self, func: ConditionCallback[CogT, UnresolvedContextT, P]) -> None:
        self.trigger_condition = func


def misc_command(
    name: str,
    *,
    description: str = "...",
    nsfw: bool = False,
    listener_name: LiteralNames | None = None,
    extras: dict[Any, Any] | None = None,
    trigger_condition: ConditionCallback[CogT, UnresolvedContextT, P] | None = None,
) -> Callable[[Callback[CogT, UnresolvedContextT, P, T]], Callback[CogT, UnresolvedContextT, P, T]]:
    """Register an event listener as a "command" that can be retrieved from the feature exporter.
    Checkers will be called within the second argument of the function (right after the Cog (self))

    Args:
        name: name of the "command"
        description (str, optional): Description of the command. Defaults to "...".
        guild_only: If feature is only on guild or not. DO NOT DO ANY CHECK. Defaults to False.
        nsfw: If the feature contains NSFW content. DO NOT DO ANY CHECK. Defaults to False.
        default_permissions:
            Default permissions needed to use the feature. DO NOT DO ANY CHECK. Defaults to None.
        listener_name :
            If the function has a specific name, set the event name here. Defaults to None.
        extras: Some extras informations. Defaults to None.

    Returns:
        A wrapped function, bound with a MiscCommand.
    """

    def inner(func: Callback[CogT, UnresolvedContextT, P, T]) -> Callback[CogT, UnresolvedContextT, P, T]:
        true_listener_name = "on_" + listener_name if listener_name else func.__name__

        misc_command = MiscCommand[CogT, P, T](
            name=name,
            callback=func,
            description=description,
            nsfw=nsfw,
            type=events_to_type[true_listener_name],
            extras=extras or {},
            trigger_condition=trigger_condition,  # type: ignore
        )

        @wraps(func)
        async def inner(cog: CogT, context: UnresolvedContext, *args: P.args, **kwargs: P.kwargs) -> T:
            return await misc_command.do_call(cog, context, *args, **kwargs)

        setattr(inner, "__listener_as_command__", misc_command)

        add_listener = commands.Cog.listener(true_listener_name)
        add_listener(inner)

        return inner

    return inner


@runtime_checkable
class MiscCommandContextRaw(Protocol):
    channel_id: int  # to work with raw events
    user_id: int


@runtime_checkable
class MiscCommandContextFilled(Protocol):
    channel: MessageableChannel
    user: discord.User


class MiscCommandContext(Generic[BotT]):
    def __init__(
        self,
        bot: BotT,
        channel: MessageableChannel,
        user: User | Member,
        command: MiscCommand[Any, ..., Any],
    ) -> None:
        self.channel: MessageableChannel = channel
        self.user: User | Member = user
        self.bot: BotT = bot
        self.command: MiscCommand[Any, ..., Any] = command

    @classmethod
    async def resolve(cls, bot: BotT, context: UnresolvedContext, command: MiscCommand[Any, ..., Any]) -> Self:
        channel: MessageableChannel
        user: User | Member

        match context:
            case discord.Message():
                channel = context.channel
                user = context.author
            case MiscCommandContextFilled():
                channel = context.channel
                user = context.user
            case MiscCommandContextRaw():
                channel = cast(
                    "MessageableChannel",
                    bot.get_channel(context.channel_id) or await bot.fetch_channel(context.channel_id),
                )
                user = bot.get_user(context.user_id) or await bot.fetch_user(context.user_id)

        return cls(bot, channel, user, command)

    @property
    def me(self) -> Member | ClientUser:
        # bot.user will never be None at this point.
        bot_user = cast(ClientUser, self.bot.user)
        return self.channel.guild.me if self.channel.guild is not None else bot_user

    @property
    def bot_permissions(self) -> Permissions:
        channel = self.channel
        if channel.type == discord.ChannelType.private:
            return Permissions._dm_permissions()  # pyright: ignore [reportPrivateUsage]
        # we are not in a DM channel at this point
        me = cast(Member, self.me)
        return channel.permissions_for(me)


def misc_guild_only() -> Callable[[T], T]:
    def predicate(ctx: MiscCommandContext[Any]) -> bool:
        if ctx.channel.guild is None:
            raise MiscNoPrivateMessage()
        return True

    def decorator(func: T) -> T:
        if hasattr(func, "__listener_as_command__"):
            misc_command: MiscCommand[Any, ..., Any] = getattr(func, "__listener_as_command__")
            misc_command.add_check(predicate)
            misc_command.guild_only = True
        else:
            if not hasattr(func, "__misc_commands_checks__"):
                setattr(func, "__misc_commands_checks__", [])
            getattr(func, "__misc_commands_checks__").append(predicate)

            setattr(func, "__misc_commands_guild_only__", True)

        return func

    return decorator


def misc_check(predicate: Callable[[MiscCommandContext[Any]], CoroT[bool] | bool]) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        if hasattr(func, "__listener_as_command__"):
            misc_command: MiscCommand[Any, ..., Any] = getattr(func, "__listener_as_command__")
            misc_command.add_check(predicate)
        else:
            if not hasattr(func, "__misc_commands_checks__"):
                setattr(func, "__misc_commands_checks__", [])
            getattr(func, "__misc_commands_checks__").append(predicate)

        return func

    return decorator


def cog_property(cog_name: str):
    """Transform a method into a property that return the cog with the name passed in argument.
    Type is not truly correct because we force it to be a Cog value while it is a property that return a Cog.

    Args:
        cog_name: the cog name to return
    """

    def inner(_: Callable[..., C]) -> C:
        @property
        def cog_getter(self: Any) -> C:  # self is a cog within the .bot attribute (because every Cog should have it)
            cog: C | None = self.bot.get_cog(cog_name)
            if cog is None:
                raise UnexpectedError(f"Cog named {cog_name} is not loaded.")
            return cog

        return cog_getter  # type: ignore

    return inner
