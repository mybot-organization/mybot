from typing import Sequence, Type

from lingua import Language as LinguaLanguage, LanguageDetectorBuilder

from core import config
from core.modules.microsoft_translation import MicrosoftTranslator

from ..languages import Language, Languages
from ..translator_abc import TranslatorAdapter

lingua_to_language = {
    LinguaLanguage.ENGLISH: Languages.british_english,
    LinguaLanguage.ARABIC: Languages.arabic,
    LinguaLanguage.CHINESE: Languages.chinese,
    LinguaLanguage.FRENCH: Languages.french,
    LinguaLanguage.GERMAN: Languages.german,
    LinguaLanguage.HINDI: Languages.hindi,
    LinguaLanguage.INDONESIAN: Languages.indonesian,
    LinguaLanguage.IRISH: Languages.irish,
    LinguaLanguage.ITALIAN: Languages.italian,
    LinguaLanguage.JAPANESE: Languages.japanese,
    LinguaLanguage.KOREAN: Languages.korean,
    LinguaLanguage.POLISH: Languages.polish,
    LinguaLanguage.PORTUGUESE: Languages.brazil_portuguese,
    LinguaLanguage.RUSSIAN: Languages.russian,
    LinguaLanguage.SPANISH: Languages.spanish,
    LinguaLanguage.TURKISH: Languages.turkish,
    LinguaLanguage.VIETNAMESE: Languages.vietnamese,
}


class Translator(TranslatorAdapter):
    def __init__(self) -> None:
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


async def get_translators() -> Type[TranslatorAdapter]:
    return Translator
