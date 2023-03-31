from __future__ import annotations

import re
from operator import eq, ge, gt, le, lt
from typing import Callable

from discord import AppCommandOptionType, Interaction
from discord.app_commands import Choice, Transformer, locale_str as __

from core.errors import NonSpecificError
from core.transformers import DateTransformer, SimpleTransformer

from .enums import Pinned
from .filters import DateFilter, Has, HasFilter, LengthFilter, PinnedFilter, RegexFilter, RoleFilter, UserFilter

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
    identifiers: dict[str, Callable[[int, int], bool]] = {
        "<": lt,
        "<=": le,
        ">": gt,
        ">=": ge,
        "=": eq,
        "": eq,
    }
    regex = re.compile(r"^(<|>|<=|>=|=|)(\d+)$")

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    async def transform(self, inter: Interaction, value: str) -> LengthFilter:
        del inter  # unused

        result = self.regex.match(value)

        if not result:
            raise NonSpecificError("Invalid length filter")

        length = int(result.group(2))

        if not (0 <= length <= 4000):
            raise NonSpecificError("A length filter must be between 0 and 4000 characters")

        test = self.identifiers[result.group(1)]
        return LengthFilter(test, length)


class BeforeTransformer(Transformer):
    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    async def transform(self, inter: Interaction, value: str) -> DateFilter:
        inner_transformer = DateTransformer()
        return DateFilter(lt, await inner_transformer.transform(inter, value))


class AfterTransformer(Transformer):
    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    async def transform(self, inter: Interaction, value: str) -> DateFilter:
        inner_transformer = DateTransformer()
        return DateFilter(gt, await inner_transformer.transform(inter, value))
