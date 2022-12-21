"""
This file contain the methods and others informations that translate's commands needs.
So, we can "easly" change the translation method (switch from an API to another...).

It need to implement:
- discord locals to emote to api-specific translation relations
- a translate function
"""

from __future__ import annotations

from typing import NamedTuple

from discord import Locale
from discord.utils import find, get

from utils.libre_translate import Language as LibreLanguage, LibreTranslate


class Relation(NamedTuple):
    name: str
    code: str
    adapter: LibreLanguage
    discord_locales: tuple[Locale, ...]
    emotes: tuple[str, ...]


# fmt: off
relations: tuple[Relation, ...] = (
    Relation(
        name='english',
        code='en',
        adapter=LibreLanguage.ENGLISH,
        discord_locales=(Locale.british_english, Locale.american_english),
        emotes=("🇦🇮", "🇦🇬", "🇦🇺", "🇧🇸", "🇧🇧", "🇧🇿", "🇧🇲", "🇧🇼", "🇮🇴", "🇨🇦", "🇰🇾", "🇨🇽", "🇨🇨", "🇨🇰", "🇩🇲", "🇫🇰", "🇫🇯", "🇬🇲",
                "🇬🇭", "🇬🇮", "🇬🇩", "🇬🇺", "🇬🇬", "🇬🇾", "🇭🇲", "🇮🇲", "🇯🇲", "🇯🇪", "🇰🇮", "🇱🇷", "🇲🇼", "🇲🇻", "🇲🇭", "🇲🇺", "🇫🇲", "🇲🇸",
                "🇳🇦", "🇳🇷", "🇳🇬", "🇳🇺", "🇳🇫", "🇲🇵", "🇵🇼", "🇵🇬", "🇵🇳", "🇷🇼", "🇸🇭", "🇰🇳", "🇱🇨", "🇻🇨", "🇸🇱", "🇸🇧", "🇬🇸", "🇸🇸",
                "🇸🇿", "🇹🇴", "🇹🇹", "🇹🇨", "🇹🇻", "🇬🇧", "🇺🇸", "🇺🇲", "🇻🇬", "🇻🇮", "🇿🇲", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ),
    Relation(
        name='arabic',
        code='ar',
        adapter=LibreLanguage.ARABIC,
        discord_locales=(),
        emotes=("🇩🇿", "🇧🇭", "🇰🇲", "🇩🇯", "🇪🇬", "🇪🇷", "🇯🇴", "🇰🇼", "🇱🇧", "🇱🇾", "🇲🇷", "🇲🇦", "🇴🇲", "🇶🇦", "🇸🇦", "🇸🇩", "🇸🇾", "🇹🇳",
                "🇦🇪", "🇪🇭", "🇾🇪"),
    ),
    Relation(
        name='chinese (simplified)',
        code='zn-cn',
        adapter=LibreLanguage.CHINESE,
        discord_locales=(Locale.chinese, Locale.taiwan_chinese),
        emotes=("🇨🇳", "🇭🇰", "🇲🇴", "🇹🇼")
    ),
    Relation(
        name='french',
        code='fr',
        adapter=LibreLanguage.FRENCH,
        discord_locales=(Locale.french,),
        emotes=("🇧🇯", "🇧🇫", "🇧🇮", "🇨🇲", "🇨🇫", "🇹🇩", "🇨🇩", "🇨🇬", "🇨🇮", "🇬🇶", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦", "🇬🇵", "🇬🇳", "🇲🇱",
                "🇲🇶", "🇾🇹", "🇲🇨", "🇳🇨", "🇳🇪", "🇷🇪", "🇧🇱", "🇲🇫", "🇵🇲", "🇸🇳", "🇸🇨", "🇹🇬", "🇻🇺", "🇼🇫")
    ),
    Relation(
        name='german',
        code='de',
        adapter=LibreLanguage.GERMAN,
        discord_locales=(Locale.german,),
        emotes=("🇦🇹", "🇩🇪", "🇱🇮", "🇨🇭")
    ),
    Relation(
        name='hindi',
        code='hi',
        adapter=LibreLanguage.HINDI,
        discord_locales=(Locale.hindi,),
        emotes=("🇮🇳",)
    ),
    Relation(
        name='indonesian',
        code='id',
        adapter=LibreLanguage.INDONESIAN,
        discord_locales=(),
        emotes=("🇮🇩",)
    ),
    Relation(
        name='irish',
        code='ga',
        adapter=LibreLanguage.IRISH,
        discord_locales=(),
        emotes=("🇮🇪",)
    ),
    Relation(
        name="italian",
        code='it',
        adapter=LibreLanguage.ITALIAN,
        discord_locales=(Locale.italian,),
        emotes=("🇮🇹", "🇸🇲", "🇻🇦")
    ),
    Relation(
        name="japanese",
        code="ja",
        adapter=LibreLanguage.JAPANESE,
        discord_locales=(Locale.japanese,),
        emotes=("🇯🇵",)
    ),
    Relation(
        name="korean",
        code="ko",
        adapter=LibreLanguage.KOREAN,
        discord_locales=(Locale.korean,),
        emotes=("🇰🇵", "🇰🇷",)
    ),
    Relation(
        name="polish",
        code="pl",
        adapter=LibreLanguage.POLISH,
        discord_locales=(Locale.polish,),
        emotes=("🇵🇱",)
    ),
    Relation(
        name="portuguese",
        code="pt",
        adapter=LibreLanguage.PORTUGUESE,
        discord_locales=(Locale.brazil_portuguese,),
        emotes=("🇦🇴", "🇧🇷", "🇨🇻", "🇬🇼", "🇲🇿", "🇵🇹", "🇸🇹", "🇹🇱")
    ),
    Relation(
        name="russian",
        code="ru",
        adapter=LibreLanguage.RUSSIAN,
        discord_locales=(Locale.russian,),
        emotes=("🇦🇶", "🇷🇺")
    ),
    Relation(
        name="spanish",
        code="es",
        adapter=LibreLanguage.SPANISH,
        discord_locales=(Locale.spain_spanish,),
        emotes=("🇦🇷", "🇧🇴", "🇨🇱", "🇨🇴", "🇨🇷", "🇨🇺", "🇩🇴", "🇪🇨", "🇸🇻", "🇬🇹", "🇭🇳", "🇲🇽", "🇳🇮", "🇵🇦", "🇵🇾", "🇵🇪", "🇵🇷", "🇪🇸", 
                "🇺🇾", "🇻🇪"),
    ),
    Relation(
        name="turk",
        code="tr",
        adapter=LibreLanguage.TURK,
        discord_locales=(Locale.turkish,),
        emotes=("🇹🇷",)
    ),
    Relation(
        name="vietnames",
        code="vi",
        adapter=LibreLanguage.VIETNAMESE,
        discord_locales=(Locale.vietnamese,),
        emotes=("🇻🇳",)
    )
)
# fmt: on


class Language(NamedTuple):
    name: str
    code: str
    adapter: LibreLanguage

    @classmethod
    def from_emote(cls, emote: str) -> Language | None:
        relation = find(lambda rel: emote in rel.emotes, relations)
        return Language(name=relation.name, code=relation.code, adapter=relation.adapter) if relation else None

    @classmethod
    def from_discord_locale(cls, locale: Locale) -> Language | None:
        relation = find(lambda rel: locale in rel.discord_locales, relations)
        return Language(name=relation.name, code=relation.code, adapter=relation.adapter) if relation else None

    @classmethod
    def from_code(cls, code: str) -> Language | None:
        relation = get(relations, code=code)
        return Language(name=relation.name, code=relation.code, adapter=relation.adapter) if relation else None

    @staticmethod
    def available_languages() -> list[Language]:
        return [Language(name=rel.name, code=rel.code, adapter=rel.adapter) for rel in relations]


# libre_translate = LibreTranslate("http://host.docker.internal:5001/")
libre_translate = LibreTranslate()


async def translate(text: str, to: Language, from_: Language | None = None) -> str:
    return await libre_translate.translate(text, to.adapter, from_.adapter if from_ else "auto")
