from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class ConfigGuild(ExtendedCog, name="config_guild"):
    async def emote(self, inter: Interaction) -> None:
        raise NotImplementedError
