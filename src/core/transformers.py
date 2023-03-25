from __future__ import annotations

from typing import Any

from discord import AppCommandOptionType, Interaction
from discord.app_commands import Transformer


class SimpleTransformer(Transformer):
    def __init__(self, return_type_constructor: Any, type: AppCommandOptionType = AppCommandOptionType.string):
        self.return_type_constructor = return_type_constructor
        self._type = type

    @property
    def type(self) -> AppCommandOptionType:
        return self._type

    async def transform(self, inter: Interaction, value: Any) -> Any:
        del inter  # unused
        return self.return_type_constructor(value)
