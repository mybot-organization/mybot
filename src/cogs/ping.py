# TODO: use TemporaryCache
# TODO: add an easter egg


from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Ping(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

    @app_commands.command(
        name=__("ping"),
        description=__("Get the bot latency."),
        extras={"soon": True},
    )
    async def ping(self, inter: Interaction) -> None:
        raise NotImplementedError()


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Ping(bot))
