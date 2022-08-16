from __future__ import annotations

import gettext
import inspect
import logging
from glob import glob
from os import path
from typing import TYPE_CHECKING, Any

from discord import Interaction, Locale, app_commands
from discord.utils import find

if TYPE_CHECKING:
    from discord.app_commands import TranslationContextTypes, locale_str

BASE_DIR = "data/"
LOCALE_DIR = "locale"
LOCALE_DEFAULT = Locale.british_english

logger = logging.getLogger(__name__)

_locales = frozenset(map(path.basename, filter(path.isdir, glob(path.join(BASE_DIR, LOCALE_DIR, "*")))))

translations: dict[Locale, gettext.NullTranslations] = {
    Locale(locale): gettext.translation("help_center", languages=(locale,), localedir=path.join(BASE_DIR, LOCALE_DIR))
    for locale in _locales
}

translations[LOCALE_DEFAULT] = gettext.NullTranslations()


class Translator(app_commands.Translator):
    async def translate(self, string: locale_str, locale: Locale, context: TranslationContextTypes) -> str:
        return i18n(str(string), _locale=locale)


def i18n(string: str, /, *args: Any, _locale: Locale | None = None, **kwargs: Any) -> str:
    if not _locale:
        caller = inspect.stack()[1].frame.f_locals
        if item := find((lambda _item: isinstance(_item[1], Interaction)), caller.items()):
            inter: Interaction = item[1]
        else:
            logger.warning("i18n function called without local from a non-command context.")
            return string

        _locale = inter.locale

    return translations.get(_locale, translations[LOCALE_DEFAULT]).gettext(string).format(*args, **kwargs)


_ = i18n
