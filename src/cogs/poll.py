from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.app_commands import locale_str as __

from core import SpecialCog
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Poll(SpecialCog["MyBot"]):
    @app_commands.command(
        name=__("poll"),
        description=__("Do a poll."),
        extras={"soon": True},
    )
    async def poll(self, inter: Interaction) -> None:
        raise NotImplementedError("Poll is not implemented.")


async def setup(bot: MyBot):
    await bot.add_cog(Poll(bot))
