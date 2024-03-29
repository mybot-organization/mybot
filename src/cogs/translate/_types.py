from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from discord import Embed, ui
from discord.utils import MISSING


class SendStrategy(Protocol):
    async def __call__(self, *, content: str = ..., embeds: Sequence[Embed] = ..., view: ui.View = MISSING) -> Any: ...


class PreSendStrategy(Protocol):
    async def __call__(self) -> Any: ...
