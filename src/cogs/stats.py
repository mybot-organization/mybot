from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Stats(ExtendedCog):
    def __init__(self, bot: MyBot):
        super().__init__(bot)
        self.temp_store: dict[int, int] = {}

    @Cog.listener()
    async def on_interaction(self, inter: Interaction) -> None:
        if inter.command is None:
            return

        command = inter.command
        app_command = get(self.bot.app_commands, name=command.name, type=discord.AppCommandType.chat_input)
        if app_command is None:
            return
        self.temp_store.setdefault(app_command.id, 0)
        self.temp_store[app_command.id] += 1

    @app_commands.command(
        name=__("stats"),
        description=__("Get some stats about the bot."),
        extras={"soon": True},
    )
    async def stats(self, inter: Interaction) -> None:
        raise NotImplementedError()


async def setup(bot: MyBot):
    await bot.add_cog(Stats(bot))
