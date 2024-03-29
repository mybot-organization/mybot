from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __

from core import ExtendedGroupCog, cog_property

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

    from .config_bot import ConfigBot
    from .config_guild import ConfigGuild


logger = logging.getLogger(__name__)

# Subcommands cannot be separated in multiple files.
# https://github.com/Rapptz/discord.py/discussions/8069
# So all commands are defined here, and their implementation are in other files.


@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
class Config(
    ExtendedGroupCog,
    group_name=__("config"),
    group_description=__("Set configurations."),
    group_extras={"beta": True},
):
    guild_group = app_commands.Group(
        name=__("guild"),
        description=__("Set configuration for the guild."),
    )
    bbot_group = app_commands.Group(
        name=__("bot"),
        description=__("Set configuration for the bot."),
    )

    @cog_property("config_guild")
    def guild_cog(self) -> ConfigGuild: ...

    @cog_property("config_bot")
    def bot_cog(self) -> ConfigBot: ...

    @guild_group.command(
        name=__("emote"),
        description=__("Add restriction to an emote for a role."),
        extras={"soon": True},
    )
    async def emote(self, inter: Interaction) -> None:
        await self.guild_cog.emote(inter)

    @bbot_group.command(
        name=__("public_translations"),
        description=__("Set if the translations are visible for everyone or not."),
    )
    async def public_translations(self, inter: Interaction, value: bool) -> None:
        await self.bot_cog.public_translation(inter, value)


async def setup(bot: MyBot) -> None:
    from .config_bot import ConfigBot
    from .config_guild import ConfigGuild

    await bot.add_cog(ConfigBot(bot))
    await bot.add_cog(ConfigGuild(bot))
    await bot.add_cog(Config(bot))
