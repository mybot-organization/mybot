"""
This file contain the methods and others informations that translate's commands needs.
So, we can "easly" change the translation method (switch from an API to another...).

It need to implement:
- discord locals to emote to api-specific translation relations
- a translate function
"""
# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false, reportUnknownArgumentType=false
# ^ because of langdetect

from __future__ import annotations

import asyncio
from typing import NamedTuple, Sequence

import langdetect
from discord import Locale
from discord.utils import find, get

from utils.libre_translate import Language as LibreLanguage, LibreTranslate


class Relation(NamedTuple):
    name: str
    code: str
    adapter: LibreLanguage
    discord_locale: Locale | None
    emotes: tuple[str, ...]


# fmt: off
relations: tuple[Relation, ...] = (
    Relation(
        name='british english',
        code='en',
        adapter=LibreLanguage.ENGLISH,
        discord_locale=Locale.british_english,
        emotes=("🇦🇮", "🇦🇬", "🇦🇺", "🇧🇸", "🇧🇧", "🇧🇿", "🇧🇲", "🇧🇼", "🇮🇴", "🇨🇦", "🇰🇾", "🇨🇽", "🇨🇨", "🇨🇰", "🇩🇲", "🇫🇰", "🇫🇯", "🇬🇲",
                "🇬🇭", "🇬🇮", "🇬🇩", "🇬🇺", "🇬🇬", "🇬🇾", "🇭🇲", "🇮🇲", "🇯🇲", "🇯🇪", "🇰🇮", "🇱🇷", "🇲🇼", "🇲🇻", "🇲🇭", "🇲🇺", "🇫🇲", "🇲🇸",
                "🇳🇦", "🇳🇷", "🇳🇬", "🇳🇺", "🇳🇫", "🇲🇵", "🇵🇼", "🇵🇬", "🇵🇳", "🇷🇼", "🇸🇭", "🇰🇳", "🇱🇨", "🇻🇨", "🇸🇱", "🇸🇧", "🇬🇸", "🇸🇸",
                "🇸🇿", "🇹🇴", "🇹🇹", "🇹🇨", "🇹🇻", "🇬🇧", "🇻🇬", "🇻🇮", "🇿🇲", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ),
    Relation(
        name='american english',
        code='en',
        adapter=LibreLanguage.ENGLISH,
        discord_locale=Locale.american_english,
        emotes=("🇺🇸", "🇺🇲"),
    ),
    Relation(
        name='arabic',
        code='ar',
        adapter=LibreLanguage.ARABIC,
        discord_locale=None,
        emotes=("🇩🇿", "🇧🇭", "🇰🇲", "🇩🇯", "🇪🇬", "🇪🇷", "🇯🇴", "🇰🇼", "🇱🇧", "🇱🇾", "🇲🇷", "🇲🇦", "🇴🇲", "🇶🇦", "🇸🇦", "🇸🇩", "🇸🇾", "🇹🇳",
                "🇦🇪", "🇪🇭", "🇾🇪"),
    ),
    Relation(
        name='chinese (simplified)',
        code='zn-cn',
        adapter=LibreLanguage.CHINESE,
        discord_locale=Locale.chinese,
        emotes=("🇨🇳", "🇭🇰", "🇲🇴", "🇹🇼")
    ),
    Relation(
        name='chinese (simplified)',
        code='zn-cn',
        adapter=LibreLanguage.CHINESE,
        discord_locale=Locale.taiwan_chinese,
        emotes=()
    ),
    Relation(
        name='french',
        code='fr',
        adapter=LibreLanguage.FRENCH,
        discord_locale=Locale.french,
        emotes=("🇧🇯", "🇧🇫", "🇧🇮", "🇨🇲", "🇨🇫", "🇹🇩", "🇨🇩", "🇨🇬", "🇨🇮", "🇬🇶", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦", "🇬🇵", "🇬🇳", "🇲🇱",
                "🇲🇶", "🇾🇹", "🇲🇨", "🇳🇨", "🇳🇪", "🇷🇪", "🇧🇱", "🇲🇫", "🇵🇲", "🇸🇳", "🇸🇨", "🇹🇬", "🇻🇺", "🇼🇫")
    ),
    Relation(
        name='german',
        code='de',
        adapter=LibreLanguage.GERMAN,
        discord_locale=Locale.german,
        emotes=("🇦🇹", "🇩🇪", "🇱🇮", "🇨🇭")
    ),
    Relation(
        name='hindi',
        code='hi',
        adapter=LibreLanguage.HINDI,
        discord_locale=Locale.hindi,
        emotes=("🇮🇳",)
    ),
    Relation(
        name='indonesian',
        code='id',
        adapter=LibreLanguage.INDONESIAN,
        discord_locale=None,
        emotes=("🇮🇩",)
    ),
    Relation(
        name='irish',
        code='ga',
        adapter=LibreLanguage.IRISH,
        discord_locale=None,
        emotes=("🇮🇪",)
    ),
    Relation(
        name="italian",
        code='it',
        adapter=LibreLanguage.ITALIAN,
        discord_locale=Locale.italian,
        emotes=("🇮🇹", "🇸🇲", "🇻🇦")
    ),
    Relation(
        name="japanese",
        code="ja",
        adapter=LibreLanguage.JAPANESE,
        discord_locale=Locale.japanese,
        emotes=("🇯🇵",)
    ),
    Relation(
        name="korean",
        code="ko",
        adapter=LibreLanguage.KOREAN,
        discord_locale=Locale.korean,
        emotes=("🇰🇵", "🇰🇷",)
    ),
    Relation(
        name="polish",
        code="pl",
        adapter=LibreLanguage.POLISH,
        discord_locale=Locale.polish,
        emotes=("🇵🇱",)
    ),
    Relation(
        name="portuguese",
        code="pt",
        adapter=LibreLanguage.PORTUGUESE,
        discord_locale=Locale.brazil_portuguese,
        emotes=("🇦🇴", "🇧🇷", "🇨🇻", "🇬🇼", "🇲🇿", "🇵🇹", "🇸🇹", "🇹🇱")
    ),
    Relation(
        name="russian",
        code="ru",
        adapter=LibreLanguage.RUSSIAN,
        discord_locale=Locale.russian,
        emotes=("🇦🇶", "🇷🇺")
    ),
    Relation(
        name="spanish",
        code="es",
        adapter=LibreLanguage.SPANISH,
        discord_locale=Locale.spain_spanish,
        emotes=("🇦🇷", "🇧🇴", "🇨🇱", "🇨🇴", "🇨🇷", "🇨🇺", "🇩🇴", "🇪🇨", "🇸🇻", "🇬🇹", "🇭🇳", "🇲🇽", "🇳🇮", "🇵🇦", "🇵🇾", "🇵🇪", "🇵🇷", "🇪🇸", 
                "🇺🇾", "🇻🇪"),
    ),
    Relation(
        name="turk",
        code="tr",
        adapter=LibreLanguage.TURK,
        discord_locale=Locale.turkish,
        emotes=("🇹🇷",)
    ),
    Relation(
        name="vietnames",
        code="vi",
        adapter=LibreLanguage.VIETNAMESE,
        discord_locale=Locale.vietnamese,
        emotes=("🇻🇳",)
    )
)
# fmt: on


class Language(NamedTuple):
    name: str
    code: str
    locale: Locale | None
    adapter: LibreLanguage

    @classmethod
    def from_emote(cls, emote: str) -> Language | None:
        relation = find(lambda rel: emote in rel.emotes, relations)
        return (
            Language(name=relation.name, code=relation.code, adapter=relation.adapter, locale=relation.discord_locale)
            if relation
            else None
        )

    @classmethod
    def from_discord_locale(cls, locale: Locale) -> Language | None:
        relation = get(relations, discord_locale=locale)
        return (
            Language(name=relation.name, code=relation.code, adapter=relation.adapter, locale=relation.discord_locale)
            if relation
            else None
        )

    @classmethod
    def from_code(cls, code: str) -> Language | None:
        relation = get(relations, code=code)
        return (
            Language(name=relation.name, code=relation.code, adapter=relation.adapter, locale=relation.discord_locale)
            if relation
            else None
        )

    @staticmethod
    def available_languages() -> list[Language]:
        return [
            Language(name=rel.name, code=rel.code, adapter=rel.adapter, locale=rel.discord_locale) for rel in relations
        ]


libre_translate = LibreTranslate()


async def translate(text: str, to: Language, from_: Language | None = None) -> str:
    return await libre_translate.translate(text, to.adapter, from_.adapter if from_ else "auto")


async def batch_translate(texts: Sequence[str], to: Language, from_: Language | None = None) -> list[str]:
    return await asyncio.gather(
        *[libre_translate.translate(text, to.adapter, from_.adapter if from_ else "auto") for text in texts]
    )


async def detect(text: str) -> Language | None:
    try:
        language = Language.from_code(langdetect.detect(text))
    except langdetect.lang_detect_exception.LangDetectException:
        return None
    else:
        return language
