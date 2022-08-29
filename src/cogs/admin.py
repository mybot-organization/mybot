from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

from utils.constants import SUPPORT_GUILD_ID

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Admin(Cog):  # TODO: add checkers
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    @app_commands.command()
    @app_commands.guilds(SUPPORT_GUILD_ID)
    async def reload_extension(self, inter: Interaction, extension: str):
        await self.bot.reload_extension(extension)
        await inter.response.send_message(f"Extension [{extension}] reloaded successfully")

    @reload_extension.autocomplete("extension")
    async def extension_autocompleter(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=ext, value=ext) for ext in self.bot.extensions_names if ext.startswith(current)
        ]

    @app_commands.command()
    @app_commands.guilds(SUPPORT_GUILD_ID)
    async def sync_tree(self, inter: Interaction):
        await inter.response.defer()
        await self.bot.sync_tree()
        await inter.edit_original_response(content=f"Tree successfully synchronized.")


async def setup(bot: MyBot):
    await bot.add_cog(Admin(bot))
