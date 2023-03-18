from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import SpecialCog

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class GameConnect4(SpecialCog["MyBot"], name="game_connect4"):
    async def connect4(self, inter: Interaction) -> None:
        raise NotImplementedError()
