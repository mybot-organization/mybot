from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands
from discord.app_commands import AppCommand, locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get

from utils import ResponseType, response_constructor
from utils.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Stats(Cog):  # TODO: add checkers
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

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

    @app_commands.command(name=__("stats"), description=__("Obtenir des stats sur le bot."))
    async def stats(self, inter: Interaction) -> None:
        embed = response_constructor(ResponseType.info, _("Quelques statistiques sur MyBot")).embed
        for c_id, v in self.temp_store.items():
            cmd = cast(AppCommand, get(self.bot.app_commands, id=c_id))
            embed.add_field(name=cmd.name, value=str(v))
        await inter.response.send_message(embed=embed)


async def setup(bot: MyBot):
    await bot.add_cog(Stats(bot))
