from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.app_commands import CommandNotFound, CommandTree

from utils import ResponseType, response_constructor
from utils.errors import BaseError, MaxConcurrencyReached
from utils.i18n import _

if TYPE_CHECKING:
    from discord.app_commands import AppCommandError

    from mybot import MyBot


logger = logging.getLogger(__name__)


class CustomCommandTree(CommandTree["MyBot"]):
    @staticmethod
    async def send_error(inter: discord.Interaction, error_message: str) -> None:
        """A function to send an error message."""
        # TODO: inter is possibly already replied.
        await inter.response.send_message(**response_constructor(ResponseType.error, error_message), ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: AppCommandError) -> None:
        """Function called when a command raise an error."""

        match error:
            case CommandNotFound():
                return
            case BaseError():
                return await self.send_error(interaction, str(error))
            case MaxConcurrencyReached():
                return await self.send_error(
                    interaction,
                    _("This command is already executed the max amount of times. (Max: {error.rate})", error=error),
                )
            case _:
                await self.send_error(interaction, _("An unhandled error happened.\n{error}", error=error))

        logger.error(f"An unhandled error happened : {error} ({type(error)})")
