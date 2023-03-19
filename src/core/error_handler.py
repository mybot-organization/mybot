from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from discord import ButtonStyle, ui
from discord.app_commands import CommandNotFound
from discord.ext import commands

from . import ResponseType, response_constructor
from .errors import BaseError, MaxConcurrencyReached
from .i18n import _

if TYPE_CHECKING:
    from discord import Interaction
    from discord.app_commands import AppCommandError

    from core.errors import MiscCommandException
    from core.misc_command import MiscCommandContext
    from mybot import MyBot

logger = logging.getLogger(__name__)


BotT = TypeVar("BotT", bound="commands.Bot | commands.AutoShardedBot")


class ErrorHandler:
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    async def send_error(self, inter: Interaction, error_message: str) -> None:
        """A function to send an error message."""
        view = ui.View()
        view.add_item(
            ui.Button(style=ButtonStyle.url, label=_("Support server"), url=(await self.bot.support_invite).url)
        )

        strategy = inter.response.send_message
        if inter.response.is_done():
            strategy = inter.followup.send
        await strategy(**response_constructor(ResponseType.error, error_message), ephemeral=True, view=view)

    async def handle_app_command_error(self, inter: Interaction, error: AppCommandError) -> None:
        match error:
            case CommandNotFound():
                return
            case BaseError():
                return await self.send_error(inter, str(error))
            case MaxConcurrencyReached():
                return await self.send_error(
                    inter,
                    _("This command is already executed the max amount of times. (Max: {error.rate})", error=error),
                )
            case _:
                await self.send_error(inter, _("An unhandled error happened.\n{error}", error=error))

        logger.error("An unhandled error happened : %s (%s)", error, type(error))

    async def handle_misc_command_error(self, context: MiscCommandContext, error: MiscCommandException) -> None:
        del context  # unused (TODO)
        logger.debug("An unhandled error happened.\n%s", error)
