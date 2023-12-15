from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class GameConnect4(ExtendedCog, name="game_connect4"):
    async def connect4(self, inter: Interaction) -> None:
        raise NotImplementedError()
