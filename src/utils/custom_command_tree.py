from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.app_commands import AppCommandError, CommandNotFound, CommandTree

from utils.errors import BaseError

if TYPE_CHECKING:
    from main import MyBot


class CustomCommandTree(CommandTree["MyBot"]):
    @staticmethod
    async def send_error(inter: discord.Interaction, error_message: str) -> None:
        """A function to send an error message."""
        embed = discord.Embed(colour=discord.Color.brand_red())
        embed.set_author(
            name=error_message,
            icon_url="https://cdn.discordapp.com/attachments/584397334608084992/1005925420639735870/discord_error_icon.png",
        )
        await inter.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: AppCommandError) -> None:
        """Function called when a command raise an error."""

        match error:
            case CommandNotFound():
                return
            case BaseError():
                return await self.send_error(interaction, str(error))
            case _:
                await self.send_error(interaction, "Une erreur inconnue est survenue.")

        self.client.logger.error(error)
