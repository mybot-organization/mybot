from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.app_commands import AppCommandError, CommandNotFound, CommandTree

from utils import ResponseType, response_constructor
from utils.errors import BaseError

if TYPE_CHECKING:
    from mybot import MyBot


logger = logging.getLogger(__name__)


class CustomCommandTree(CommandTree["MyBot"]):
    @staticmethod
    async def send_error(inter: discord.Interaction, error_message: str) -> None:
        """A function to send an error message."""
        await inter.response.send_message(**response_constructor(ResponseType.error, error_message), ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: AppCommandError) -> None:
        """Function called when a command raise an error."""

        match error:
            case CommandNotFound():
                return
            case BaseError():
                return await self.send_error(interaction, str(error))
            case _:
                await self.send_error(interaction, "Une erreur inconnue est survenue.")

        logger.error(error)
