from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class GameConnect4(Cog, name="game_connect4"):
    def __init__(self, bot: MyBot):
        self.bot = bot

    async def connect4(self, inter: Interaction) -> None:
        raise NotImplementedError()
