from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands

from core import ExtendedCog, config
from core.checkers import is_me

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

logger = logging.getLogger(__name__)


class Admin(ExtendedCog):
    @app_commands.command()
    @app_commands.guilds(config.support_guild_id)
    @is_me
    async def reload_extension(self, inter: Interaction, extension: str):
        await self.bot.reload_extension(extension)
        await inter.response.send_message(f"Extension [{extension}] reloaded successfully")

    @reload_extension.autocomplete("extension")
    async def extension_autocompleter(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=ext, value=f"cogs.{ext}")
            for ext in self.bot.config.extensions
            if ext.startswith(current)
        ]

    @app_commands.command()
    @app_commands.guilds(config.support_guild_id)
    @is_me
    async def sync_tree(self, inter: Interaction):
        await inter.response.defer()
        await self.bot.sync_tree()
        await inter.edit_original_response(content="Tree successfully synchronized.")


async def setup(bot: MyBot):
    await bot.add_cog(Admin(bot))
