from __future__ import annotations

import gettext
import inspect
import logging
from glob import glob
from os import path
from typing import TYPE_CHECKING, Any

from discord import Interaction, Locale, app_commands
from discord.utils import MISSING, find

from core.constants import TranslationContextLimits

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
        char_limit = TranslationContextLimits.from_location(context.location)
        if char_limit and len(new_string) > char_limit.value:
            logger.warning(
                "The translated string is too long: %s from %s\n%s",
                context.location,
                context.data.name,
                new_string,
            )
            new_string = new_string[: char_limit.value - 1] + "…"
        return new_string


def i18n(
    string: str,
    /,
    *args: Any,
    _locale: Locale | None = MISSING,
    _silent: bool = False,
    _l: int = -1,  # size limit
    **kwargs: Any,
) -> str:
    if _silent:
        logger.warning("Deprecated usage of _silent parameter in i18n function.")
        _locale = None
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
            if not _silent:
                logger.warning("i18n function cannot retrieve an interaction for this string.\nstring=%s", string)
            return string

        _locale = inter.locale
    if _locale is None:
        result = string.format(*args, **kwargs)
    else:
        result = translations.get(_locale, translations[LOCALE_DEFAULT]).gettext(string).format(*args, **kwargs)

    if _l > 0 and len(result) > _l:
        logger.warning("The translated and formatted string is too long: %s\n%s", string, result)
        result = result[: _l - 1] + "…"
    return result


_ = i18n

load_translations()
