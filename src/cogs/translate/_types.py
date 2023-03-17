from __future__ import annotations

from typing import Any, Protocol, Sequence

from discord import Embed, ui
from discord.utils import MISSING


class SendStrategy(Protocol):
    async def __call__(self, *, content: str = Any, embeds: Sequence[Embed] = Any, view: ui.View = MISSING) -> Any:
        ...


class PreSendStrategy(Protocol):
    async def __call__(self) -> Any:
        ...
