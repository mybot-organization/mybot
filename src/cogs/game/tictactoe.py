from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class GameTictactoe(ExtendedCog, name="game_tictactoe"):
    async def tictactoe(self, inter: Interaction) -> None:
        raise NotImplementedError
