from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get

from commands_exporter import features_to_dict
from utils import ResponseType, response_constructor
from utils.constants import Emojis
from utils.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Help(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

        self.bot.loop.create_task(self.load_features_info())

    async def load_features_info(self):
        if not self.bot.is_ready():
            await self.bot.wait_for("ready")
        self.features_infos = features_to_dict(self.bot)

    @app_commands.command(name=__("help"), description=__("Get help about the bot."), extras={"beta": True})
    async def _help(self, inter: Interaction):
        beta = Emojis.beta_1 + Emojis.beta_2

        embed = response_constructor(ResponseType.info, _("Commands of MyBot"))["embed"]
        description = ""

        for slash_command in self.features_infos.slash_commands:
            app_command = get(self.bot.app_commands, name=slash_command.name, type=discord.AppCommandType.chat_input)
            if app_command is None:
                logger.warning(f"Command {slash_command.name} didn't get its app_command for some reason.")
                continue
            description += f"</{slash_command.name}:{app_command.id}>\n{_(slash_command.description)} {beta * slash_command.beta}\n\n"

        embed.add_field(name=_("Chat input commands"), value=description)

        print(self.features_infos.slash_commands)
        print(self.bot.tree.get_commands())
        await inter.response.send_message(embed=embed)


async def setup(bot: MyBot):
    await bot.add_cog(Help(bot))
