from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self, Sequence, TypeVar

from discord.ext import commands

from .misc_command import MiscCommand

if TYPE_CHECKING:
    from discord.abc import Snowflake
    from discord.ext.commands.bot import AutoShardedBot, Bot, BotBase  # pyright: ignore[reportMissingTypeStubs]

_BotType = TypeVar("_BotType", bound="Bot | AutoShardedBot")


class SpecialCog(commands.Cog, Generic[_BotType]):
    __cog_misc_commands__: list[MiscCommand[Any, ..., Any]]
    bot: _BotType

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        cls = super().__new__(cls, *args, **kwargs)

        cls.__cog_misc_commands__ = []
        for _, listener in cls.__cog_listeners__:
            misc_command = getattr(getattr(cls, listener), "__listener_as_command__", None)
            if isinstance(misc_command, MiscCommand):
                cls.__cog_misc_commands__.append(misc_command)  # pyright: ignore [reportUnknownArgumentType]

        return cls

    def __init__(self, bot: _BotType) -> None:
        self.bot = bot

    def get_misc_commands(self) -> list[MiscCommand[Any, ..., Any]]:
        """Return all the misc commands in this cog."""
        return list(self.__cog_misc_commands__)

    async def _inject(self, bot: BotBase, override: bool, guild: Snowflake | None, guilds: Sequence[Snowflake]) -> Self:
        self = await super()._inject(bot, override, guild, guilds)

        # bind the bot to the misc commands
        # used to dispatch error for error handling
        for misc_command in self.get_misc_commands():
            misc_command.bot = bot  # type: ignore

        return self


class SpecialGroupCog(SpecialCog[_BotType]):
    __cog_is_app_commands_group__: ClassVar[bool] = True
