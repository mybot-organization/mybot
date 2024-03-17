from collections.abc import Sequence

from lingua import Language as LinguaLanguage, LanguageDetectorBuilder

from core import config
from libraries.microsoft_translation import MicrosoftTranslator

from ..languages import Language, Languages, LanguagesEnum
from ..translator_abc import TranslatorAdapter

lingua_to_language = {
    LinguaLanguage.ENGLISH: LanguagesEnum.british_english,
    LinguaLanguage.ARABIC: LanguagesEnum.arabic,
    LinguaLanguage.CHINESE: LanguagesEnum.chinese,
    LinguaLanguage.FRENCH: LanguagesEnum.french,
    LinguaLanguage.GERMAN: LanguagesEnum.german,
    LinguaLanguage.HINDI: LanguagesEnum.hindi,
    LinguaLanguage.INDONESIAN: LanguagesEnum.indonesian,
    LinguaLanguage.IRISH: LanguagesEnum.irish,
    LinguaLanguage.ITALIAN: LanguagesEnum.italian,
    LinguaLanguage.JAPANESE: LanguagesEnum.japanese,
    LinguaLanguage.KOREAN: LanguagesEnum.korean,
    LinguaLanguage.POLISH: LanguagesEnum.polish,
    LinguaLanguage.PORTUGUESE: LanguagesEnum.brazil_portuguese,
    LinguaLanguage.RUSSIAN: LanguagesEnum.russian,
    LinguaLanguage.SPANISH: LanguagesEnum.spanish,
    LinguaLanguage.TURKISH: LanguagesEnum.turkish,
    LinguaLanguage.VIETNAMESE: LanguagesEnum.vietnamese,
}


class Translator(TranslatorAdapter):
    def __init__(self) -> None:
        if config.MS_TRANSLATE_KEY is None or config.MS_TRANSLATE_REGION is None:
            raise ValueError("Missing Microsoft Translator configuration")
        self.instance = MicrosoftTranslator(config.MS_TRANSLATE_KEY, config.MS_TRANSLATE_REGION)
        self.detector = (
            LanguageDetectorBuilder.from_languages(*lingua_to_language.keys())
            .with_low_accuracy_mode()
            .with_minimum_relative_distance(0.8)
            .build()
        )

    async def close(self):
        await self.instance.close()

    async def translate(self, text: str, to: Language, from_: Language | None = None) -> str:
        result = await self.instance.translate([text], to.lang_code, from_.lang_code if from_ else None)
        return result[0].value[0].text

    async def batch_translate(self, texts: Sequence[str], to: Language, from_: Language | None = None) -> list[str]:
        result = await self.instance.translate(texts, to.lang_code, from_.lang_code if from_ else None)
        return [r.value[0].text for r in result]

    async def detect(self, text: str) -> Language | None:
        if (result := self.detector.detect_language_of(text)) is None:
            return None
        return lingua_to_language[result].value

    async def available_languages(self) -> Languages:
        return Languages(x.value for x in LanguagesEnum)


def get_translator() -> type[TranslatorAdapter]:
    return Translator
