from __future__ import annotations

from discord import AppCommandOptionType, Interaction
from discord.app_commands import Choice, Transformer, locale_str as __

from core.transformers import SimpleTransformer

from .enums import Pinned
from .filters import PinnedFilter, RegexFilter, RoleFilter, UserFilter

RegexTransformer = SimpleTransformer(RegexFilter.from_string)
UserTransformer = SimpleTransformer(UserFilter.from_user, AppCommandOptionType.user)
RoleTransformer = SimpleTransformer(RoleFilter.from_role, AppCommandOptionType.role)


class PinnedTransformer(Transformer):
    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.integer

    @property
    def choices(self) -> list[Choice[int | float | str]]:
        return [
            Choice(name=__("include"), value=Pinned.include.value),
            Choice(name=__("exclude"), value=Pinned.exclude.value),
            Choice(name=__("only"), value=Pinned.only.value),
        ]

    async def transform(self, inter: Interaction, value: Pinned) -> PinnedFilter:
        return PinnedFilter(value)
