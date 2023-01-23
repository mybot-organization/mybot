from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discord.app_commands import CommandTree

from .i18n import _

if TYPE_CHECKING:
    from discord import Interaction
    from discord.app_commands import AppCommandError

    from mybot import MyBot


logger = logging.getLogger(__name__)


class CustomCommandTree(CommandTree["MyBot"]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @property
    def active_guild_ids(self) -> set[int]:
        return self._guild_commands.keys() | {g for _, g, _ in self._context_menus if g is not None}  # type: ignore

    async def on_error(self, interaction: Interaction, error: AppCommandError) -> None:
        """Function called when a command raise an error."""
        await self.client.error_handler.handle_app_command_error(interaction, error)
