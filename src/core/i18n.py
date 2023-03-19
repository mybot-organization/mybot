from __future__ import annotations

import gettext
import inspect
import logging
from glob import glob
from os import path
from typing import TYPE_CHECKING, Any

from discord import Interaction, Locale, app_commands
from discord.utils import MISSING, find

if TYPE_CHECKING:
    from types import FrameType

    from discord.app_commands import TranslationContextTypes, locale_str

BASE_DIR = "."
LOCALE_DIR = "locale"
LOCALE_DEFAULT = Locale.british_english

logger = logging.getLogger(__name__)

translations: dict[Locale, gettext.GNUTranslations | gettext.NullTranslations] = {}


def load_translations():
    global translations

    _locales = frozenset(map(path.basename, filter(path.isdir, glob(path.join(BASE_DIR, LOCALE_DIR, "*")))))

    translations = {
        Locale(locale): gettext.translation("mybot", languages=(locale,), localedir=path.join(BASE_DIR, LOCALE_DIR))
        for locale in _locales
    }

    translations[LOCALE_DEFAULT] = gettext.NullTranslations()


class Translator(app_commands.Translator):
    async def translate(self, string: locale_str, locale: Locale, context: TranslationContextTypes) -> str:
        new_string = i18n(str(string), _locale=locale)
        if context.location is app_commands.TranslationContextLocation.parameter_description:
            if len(new_string) > 100:
                logger.warning(
                    f"The translated string is too long: {context.location} for {context.data.name} from {context.data.command.name}\n{new_string}"
                )
                new_string = new_string[:99] + "…"
        return new_string


def i18n(string: str, /, *args: Any, _locale: Locale | None = MISSING, **kwargs: Any) -> str:
    if _locale is MISSING:
        frame: FrameType | None = inspect.currentframe()

        while frame is not None:
            inter: Interaction | None = find((lambda _item: isinstance(_item, Interaction)), frame.f_locals.values())
            if inter is not None:
                del frame
                break
            frame = frame.f_back
        else:
            inter = None

        if inter is None:
            logger.warning("i18n function cannot retrieve an interaction for this string.\nstring=%s", string)
            return string

        _locale = inter.locale
    if _locale is None:
        return string

    return translations.get(_locale, translations[LOCALE_DEFAULT]).gettext(string).format(*args, **kwargs)


_ = i18n

load_translations()
