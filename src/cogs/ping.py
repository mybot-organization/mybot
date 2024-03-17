# TODO(airo.pi_): use TemporaryCache
# TODO(airo.pi_): add an Easter egg


from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Ping(ExtendedCog):
    @app_commands.command(
        name=__("ping"),
        description=__("Get the bot latency."),
        extras={"soon": True},
    )
    async def ping(self, inter: Interaction) -> None:
        raise NotImplementedError


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Ping(bot))
