from enum import Enum
from typing import NamedTuple, Sequence

from discord import Locale


class Language(NamedTuple):
    name: str
    unicode_flag_emotes: Sequence[str]
    discord_locale: Locale | None = None
    _ietf_bcp_47: str | None = None

    @property
    def lang_code(self) -> str:
        return self._ietf_bcp_47 or self.discord_locale.value  # pyright: ignore [reportOptionalMemberAccess]

    def __eq__(self, e: object) -> bool:
        return isinstance(e, Language) and e.name == self.name

    def __hash__(self) -> int:
        return hash((self.name, self.lang_code))


class Languages(Enum):
    @classmethod
    def from_locale(cls, locale: Locale) -> Language:
        return next(x.value for x in Languages if x.value.discord_locale == locale)

    @classmethod
    def from_code(cls, lang_code: str) -> Language | None:
        return next((x.value for x in cls if x.value.lang_code == lang_code), None)

    @classmethod
    def from_emote(cls, unicode_emote_flag: str) -> Language | None:
        return next((x.value for x in cls if unicode_emote_flag in x.value.unicode_flag_emotes), None)

    # fmt: off
    british_english = Language(
        name='british english',
        discord_locale=Locale.british_english,
        unicode_flag_emotes=("🇦🇮", "🇦🇬", "🇦🇺", "🇧🇸", "🇧🇧", "🇧🇿", "🇧🇲", "🇧🇼", "🇮🇴", "🇨🇦", "🇰🇾", "🇨🇽", "🇨🇨", "🇨🇰", "🇩🇲", "🇫🇰",
                             "🇫🇯", "🇬🇲", "🇬🇭", "🇬🇮", "🇬🇩", "🇬🇺", "🇬🇬", "🇬🇾", "🇭🇲", "🇮🇲", "🇯🇲", "🇯🇪", "🇰🇮", "🇱🇷", "🇲🇼", "🇲🇻",
                             "🇲🇭", "🇲🇺", "🇫🇲", "🇲🇸", "🇳🇦", "🇳🇷", "🇳🇬", "🇳🇺", "🇳🇫", "🇲🇵", "🇵🇼", "🇵🇬", "🇵🇳", "🇷🇼", "🇸🇭", "🇰🇳",
                             "🇱🇨", "🇻🇨", "🇸🇱", "🇸🇧", "🇬🇸", "🇸🇸", "🇸🇿", "🇹🇴", "🇹🇹", "🇹🇨", "🇹🇻", "🇬🇧", "🇻🇬", "🇻🇮", "🇿🇲", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    )
    american_english = Language(
        name='american english',
        discord_locale=Locale.american_english,
        unicode_flag_emotes=("🇺🇸", "🇺🇲"),
    ),
    arabic = Language(
        name='arabic',
        _ietf_bcp_47='ar-SA',
        unicode_flag_emotes=("🇩🇿", "🇧🇭", "🇰🇲", "🇩🇯", "🇪🇬", "🇪🇷", "🇯🇴", "🇰🇼", "🇱🇧", "🇱🇾", "🇲🇷", "🇲🇦", "🇴🇲", "🇶🇦", "🇸🇦", "🇸🇩",
                             "🇸🇾", "🇹🇳", "🇦🇪", "🇪🇭", "🇾🇪"),
    )
    chinese = Language(
        name='chinese',
        discord_locale=Locale.chinese,
        unicode_flag_emotes=("🇨🇳", "🇭🇰", "🇲🇴", "🇹🇼")
    )
    taiwan_chinese = Language(
        name='chinese (taiwan)',
        discord_locale=Locale.taiwan_chinese,
        unicode_flag_emotes=()
    )
    french = Language(
        name='french',
        discord_locale=Locale.french,
        unicode_flag_emotes=("🇧🇯", "🇧🇫", "🇧🇮", "🇨🇲", "🇨🇫", "🇹🇩", "🇨🇩", "🇨🇬", "🇨🇮", "🇬🇶", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦", "🇬🇵",
                             "🇬🇳", "🇲🇱", "🇲🇶", "🇾🇹", "🇲🇨", "🇳🇨", "🇳🇪", "🇷🇪", "🇧🇱", "🇲🇫", "🇵🇲", "🇸🇳", "🇸🇨", "🇹🇬", "🇻🇺", "🇼🇫")
    )
    german = Language(
        name='german',
        discord_locale=Locale.german,
        unicode_flag_emotes=("🇦🇹", "🇩🇪", "🇱🇮", "🇨🇭")
    )
    hindi = Language(
        name='hindi',
        discord_locale=Locale.hindi,
        unicode_flag_emotes=("🇮🇳",)
    )
    indonesian = Language(
        name='indonesian',
        _ietf_bcp_47='id-ID',
        unicode_flag_emotes=("🇮🇩",)
    )
    irish = Language(
        name='irish',
        _ietf_bcp_47='en-IE',
        unicode_flag_emotes=("🇮🇪",)
    )
    italian = Language(
        name="italian",
        discord_locale=Locale.italian,
        unicode_flag_emotes=("🇮🇹", "🇸🇲", "🇻🇦")
    )
    japanese = Language(
        name="japanese",
        discord_locale=Locale.japanese,
        unicode_flag_emotes=("🇯🇵",)
    )
    korean = Language(
        name="korean",
        discord_locale=Locale.korean,
        unicode_flag_emotes=("🇰🇵", "🇰🇷",)
    )
    polish = Language(
        name="polish",
        discord_locale=Locale.polish,
        unicode_flag_emotes=("🇵🇱",)
    ),
    brazil_portuguese = Language(
        name="brazil portuguese",
        discord_locale=Locale.brazil_portuguese,
        unicode_flag_emotes=("🇦🇴", "🇧🇷", "🇨🇻", "🇬🇼", "🇲🇿", "🇵🇹", "🇸🇹", "🇹🇱")
    ),
    russian = Language(
        name="russian",
        discord_locale=Locale.russian,
        unicode_flag_emotes=("🇦🇶", "🇷🇺")
    ),
    spanish = Language(
        name="spanish",
        discord_locale=Locale.spain_spanish,
        unicode_flag_emotes=("🇦🇷", "🇧🇴", "🇨🇱", "🇨🇴", "🇨🇷", "🇨🇺", "🇩🇴", "🇪🇨", "🇸🇻", "🇬🇹", "🇭🇳", "🇲🇽", "🇳🇮", "🇵🇦", "🇵🇾", "🇵🇪", "🇵🇷", "🇪🇸", 
                "🇺🇾", "🇻🇪"),
    ),
    turkish = Language(
        name="turk",
        discord_locale=Locale.turkish,
        unicode_flag_emotes=("🇹🇷",)
    ),
    vietnamese = Language(
        name="vietnames",
        discord_locale=Locale.vietnamese,
        unicode_flag_emotes=("🇻🇳",)
    )


# fmt: on
