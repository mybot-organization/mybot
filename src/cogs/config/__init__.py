from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import GroupCog  # pyright: ignore[reportMissingTypeStubs]

from core import cog_property
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

    from .config_bot import ConfigBot
    from .config_guild import ConfigGuild


logger = logging.getLogger(__name__)

# Subcommands cannot be seperated in multiple files.
# https://github.com/Rapptz/discord.py/discussions/8069
# So all commands are defined here, and their implementation are in other files.


class Config(GroupCog, group_name=__("config"), group_description=__("Set configurations.")):
    guild_group = app_commands.Group(name=__("guild"), description=__("Set configuration for the guild."))
    bbot_group = app_commands.Group(name=__("bot"), description=__("Set configuration for the bot."))

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    @cog_property("config_guild")
    def guild_cog(self) -> ConfigGuild:
        ...

    @cog_property("config_bot")
    def bot_cog(self) -> ConfigBot:
        ...

    @guild_group.command(
        name=__("emote"),
        description=__("Add restriction to an emote for a role."),
        extras={"soon": True},
    )
    @app_commands.guild_only()
    @app_commands.default_permissions()  # TODO: set permissions
    async def emote(self, inter: Interaction) -> None:
        await self.guild_cog.emote(inter)


async def setup(bot: MyBot) -> None:
    from .config_bot import ConfigBot
    from .config_guild import ConfigGuild

    await bot.add_cog(ConfigBot(bot))
    await bot.add_cog(ConfigGuild(bot))
    await bot.add_cog(Config(bot))
