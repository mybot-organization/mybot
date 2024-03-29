from __future__ import annotations

from operator import ge, le
from typing import Literal

from discord import AppCommandOptionType, Interaction
from discord.app_commands import Choice, Transformer, locale_str as __

from core.errors import NonSpecificError
from core.transformers import SimpleTransformer

from .enums import Pinned
from .filters import Has, HasFilter, LengthFilter, PinnedFilter, RegexFilter, RoleFilter, UserFilter

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

    async def transform(self, inter: Interaction, value: int) -> PinnedFilter:
        del inter  # unused
        return PinnedFilter(Pinned(value))


class HasTransformer(Transformer):
    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.integer

    @property
    def choices(self) -> list[Choice[int | float | str]]:
        return [
            Choice(name=__("image"), value=Has.image.value),
            Choice(name=__("video"), value=Has.video.value),
            Choice(name=__("audio"), value=Has.audio.value),
            Choice(name=__("stickers"), value=Has.stickers.value),
            Choice(name=__("file"), value=Has.files.value),
            Choice(name=__("embed"), value=Has.embed.value),
            Choice(name=__("link (any URL)"), value=Has.link.value),
            Choice(name=__("mention"), value=Has.mention.value),
            Choice(name=__("discord invitation"), value=Has.discord_invite.value),
        ]

    async def transform(self, inter: Interaction, value: int) -> HasFilter:
        del inter  # unused
        return HasFilter(Has(value))


class LengthTransformer(Transformer):
    def __init__(self, mode: Literal["min", "max"]):
        self.mode = mode

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.integer

    @property
    def min_value(self) -> int:
        return 1

    @property
    def max_value(self) -> int:
        return 4000

    async def transform(self, inter: Interaction, value: int) -> LengthFilter:
        del inter  # unused

        if not 0 <= value <= 4000:
            raise NonSpecificError("A length filter must be between 0 and 4000 characters")

        if self.mode == "min":
            return LengthFilter(ge, value)
        else:
            return LengthFilter(le, value)
