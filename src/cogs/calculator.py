# TODO : use an autocompleter for the initial expression


from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot

logger = logging.getLogger(__name__)


class Calculator(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    @app_commands.command(
        name=__("calculator"),
        description=__("Show a calculator you can use."),
        extras={"soon": True},
    )
    async def calculator(self, inter: Interaction, initial_expression: str) -> None:
        raise NotImplementedError("Calculator is not implemented.")


async def setup(bot: MyBot):
    await bot.add_cog(Calculator(bot))
