from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class GameRPC(Cog, name="game_rpc"):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    async def rpc(self, inter: Interaction) -> None:
        raise NotImplementedError()
