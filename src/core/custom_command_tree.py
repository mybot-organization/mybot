from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discord import ButtonStyle, ui
from discord.app_commands import CommandNotFound, CommandTree
from discord.utils import get

from . import ResponseType, response_constructor
from .errors import BaseError, MaxConcurrencyReached
from .i18n import _

if TYPE_CHECKING:
    from discord import Interaction, Invite
    from discord.app_commands import AppCommandError

    from mybot import MyBot


logger = logging.getLogger(__name__)


class CustomCommandTree(CommandTree["MyBot"]):
    def __init__(self, *args: Any, **kwargs: Any):
        self._invite: Invite | None = None
        super().__init__(*args, **kwargs)

    @property
    def active_guild_ids(self) -> set[int]:
        return self._guild_commands.keys() | {g for _, g, _ in self._context_menus if g is not None}  # type: ignore

    @property
    async def _support_invite(self) -> Invite:
        if self._invite is None:
            self._invite = get(await self.client.support.invites(), max_age=0, max_uses=0, inviter=self.client.user)

        if self._invite is None:  # If invite is STILL None
            if tmp := self.client.support.rules_channel:
                channel = tmp
            else:
                channel = self.client.support.channels[0]

            self._invite = await channel.create_invite(reason="Support guild invite.")

        return self._invite

    async def send_error(self, inter: Interaction, error_message: str) -> None:
        """A function to send an error message."""
        view = ui.View()
        view.add_item(ui.Button(style=ButtonStyle.url, label=_("Support server"), url=(await self._support_invite).url))

        strategy = inter.response.send_message
        if inter.response.is_done():
            strategy = inter.followup.send
        await strategy(**response_constructor(ResponseType.error, error_message), ephemeral=True, view=view)

    async def on_error(self, interaction: Interaction, error: AppCommandError) -> None:
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
