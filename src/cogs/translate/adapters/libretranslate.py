from __future__ import annotations

import asyncio
from typing import TypeVar
from collections.abc import Sequence

from lingua import Language as LinguaLanguage, LanguageDetectorBuilder

from libraries.libre_translate import Language as LibreLanguage, LibreTranslate

from ..languages import Language, Languages, LanguagesEnum
from ..translator_abc import TranslatorAdapter

T = TypeVar("T")


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

language_to_libre = {
    LanguagesEnum.british_english: LibreLanguage.ENGLISH,
    LanguagesEnum.arabic: LibreLanguage.ARABIC,
    LanguagesEnum.chinese: LibreLanguage.CHINESE,
    LanguagesEnum.french: LibreLanguage.FRENCH,
    LanguagesEnum.german: LibreLanguage.GERMAN,
    LanguagesEnum.hindi: LibreLanguage.HINDI,
    LanguagesEnum.indonesian: LibreLanguage.INDONESIAN,
    LanguagesEnum.irish: LibreLanguage.IRISH,
    LanguagesEnum.italian: LibreLanguage.ITALIAN,
    LanguagesEnum.japanese: LibreLanguage.JAPANESE,
    LanguagesEnum.korean: LibreLanguage.KOREAN,
    LanguagesEnum.polish: LibreLanguage.POLISH,
    LanguagesEnum.brazil_portuguese: LibreLanguage.PORTUGUESE,
    LanguagesEnum.russian: LibreLanguage.RUSSIAN,
    LanguagesEnum.spanish: LibreLanguage.SPANISH,
    LanguagesEnum.turkish: LibreLanguage.TURK,
    LanguagesEnum.vietnamese: LibreLanguage.VIETNAMESE,
}


class Translator(TranslatorAdapter):
    def __init__(self):
        self.instance = LibreTranslate("https://translate.argosopentech.com/")
        self.detector = (
            LanguageDetectorBuilder.from_languages(*lingua_to_language.keys())
            .with_low_accuracy_mode()
            .with_minimum_relative_distance(0.8)
            .build()
        )

    async def available_languages(self) -> Languages:
        return Languages(x.value for x in language_to_libre.keys())

    async def translate(self, text: str, to: Language, from_: Language | None = None) -> str:
        return await self.instance.translate(
            text, language_to_libre[LanguagesEnum(to)], language_to_libre[LanguagesEnum(from_)] if from_ else "auto"
        )

    async def batch_translate(self, texts: Sequence[str], to: Language, from_: Language | None = None) -> list[str]:
        return await asyncio.gather(
            *[
                self.instance.translate(
                    text,
                    language_to_libre[LanguagesEnum(to)],
                    language_to_libre[LanguagesEnum(from_)] if from_ else "auto",
                )
                for text in texts
            ]
        )

    async def detect(self, text: str) -> Language | None:
        if (result := self.detector.detect_language_of(text)) is None:
            return None
        return lingua_to_language[result].value


def get_translator() -> type[TranslatorAdapter]:
    return Translator
