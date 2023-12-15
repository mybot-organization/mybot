from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class GameRPC(ExtendedCog, name="game_rpc"):
    async def rpc(self, inter: Interaction) -> None:
        raise NotImplementedError()
