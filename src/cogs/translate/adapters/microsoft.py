from typing import Type

from core.modules.microsoft_translation import MicrosoftTranslator

from ..adapter import LanguageAdapter, TranslatorAdapter


class Language(LanguageAdapter):
    pass


class Translator(TranslatorAdapter):
    pass


async def get_translators() -> tuple[Type[LanguageAdapter], Type[TranslatorAdapter]]:
    return Language, Translator
