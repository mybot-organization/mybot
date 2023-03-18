from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import SpecialCog

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class ConfigGuild(SpecialCog["MyBot"], name="config_guild"):
    async def emote(self, inter: Interaction) -> None:
        raise NotImplementedError()
