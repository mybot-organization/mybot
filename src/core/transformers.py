from __future__ import annotations

import datetime
from typing import Any

from dateutil.parser import parse
from discord import AppCommandOptionType, Interaction
from discord.app_commands import Transformer
from discord.utils import snowflake_time


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


class DateTransformer(Transformer):
    @property
    def type(self):
        return AppCommandOptionType.string

    async def transform(self, inter: Interaction, value: str) -> datetime.datetime:
        del inter  # unused
        if value.isdigit():
            if len(value) > 17:
                return snowflake_time(int(value))
            return datetime.datetime.fromtimestamp(int(value), tz=datetime.UTC)
        dt = parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.UTC)
        return dt
