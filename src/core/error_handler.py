from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Literal, TypeVar

from discord import ButtonStyle, Interaction, ui
from discord.app_commands.errors import AppCommandError, CommandNotFound, NoPrivateMessage
from discord.ext import commands

from . import ResponseType, response_constructor
from .errors import (
    BadArgument,
    BotMissingPermissions,
    BotUserNotPresent,
    MaxConcurrencyReached,
    MiscNoPrivateMessage,
    NonSpecificError,
)
from .extended_commands import MiscCommandContext
from .i18n import i18n

if TYPE_CHECKING:
    from core.errors import MiscCommandError
    from core.extended_commands import MiscCommandContext
    from mybot import MyBot

logger = logging.getLogger(__name__)
_ = functools.partial(i18n, _silent=True)

BotT = TypeVar("BotT", bound="commands.Bot | commands.AutoShardedBot")


class ErrorHandler:
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    async def send_error(self, ctx: Interaction | MiscCommandContext[MyBot], error_message: str) -> None:
        match ctx:
            case Interaction():
                strategy = functools.partial(ctx.response.send_message, ephemeral=True)
                if ctx.response.is_done():
                    strategy = functools.partial(ctx.followup.send, ephemeral=True)
            case MiscCommandContext():
                strategy = ctx.user.send

        view = ui.View()
        view.add_item(
            ui.Button(style=ButtonStyle.url, label=_("Support server"), url=(await self.bot.support_invite).url)
        )

        await strategy(**response_constructor(ResponseType.error, error_message), view=view)

    async def handle(self, ctx: Interaction | MiscCommandContext[MyBot], error: Exception) -> None | Literal[False]:
        match error:
            case CommandNotFound():  # Interactions only
                return None
            case NonSpecificError():
                return await self.send_error(ctx, str(error))
            case MaxConcurrencyReached():  # Interactions only (atm)
                return await self.send_error(
                    ctx,
                    _("This command is already executed the max amount of times. (Max: {error.rate})", error=error),
                )
            case BotMissingPermissions():
                return await self.send_error(
                    ctx, _("The bot is missing some permissions.\n`{}`", "`, `".join(error.missing_perms))
                )
            case BadArgument():  # Interactions only
                # TODO(airo.pi_): improve this ?
                return await self.send_error(ctx, _("You provided a bad argument."))
            case BotUserNotPresent():
                return await self.send_error(
                    ctx,
                    _(
                        "It looks like the bot has been added incorrectly. Please ask an admin to re-add the bot.",
                        _l=256,
                    ),
                )
            case MiscNoPrivateMessage() | NoPrivateMessage():
                return await self.send_error(ctx, _("This command cannot be used in DMs."))
            # case CheckFailure() | MiscCheckFailure():
            #     return await self.send_error(ctx, _("This command needs some conditions you don't meet."))
            case _:
                await self.send_error(
                    ctx, _("An unhandled error happened.\nPlease ask on the support server!", error=error)
                )
                logger.error("An unhandled error happened : %s (%s)", error, type(error))

    async def handle_app_command_error(self, inter: Interaction, error: AppCommandError) -> None:
        await self.handle(inter, error)

    async def handle_misc_command_error(self, context: MiscCommandContext[MyBot], error: MiscCommandError) -> None:
        await self.handle(context, error)
