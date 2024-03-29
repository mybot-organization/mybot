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
    """Function to translate a string.

    All strings should be passed through this function to be translated.
    Most of the time, this function will be called from a function that has an interaction as an argument.

        ```py
        @app_command.command()
        async def test(self, inter: Interaction):
            await inter.response.send_message(_("Hello, World!"))
        ```

    When doing so, the function will automatically detect the user's locale and translate the string accordingly.
    This function also supports string formatting.

        ```py
        def second_function():
            return _("Note that this will also catch the Interaction object if it is called from a command callback.")

        @app_command.command()
        async def test(self, inter: Interaction):
            await inter.response.send_message(_("Hello, {0}!", "World"))
            await inter.followup.send(content=_("Hello, {world}!", world="World"))
            await inter.followup.send(content=second_function())
        ```

    If you are not calling this function from an interaction callback, you can manually set the locale with the
    `_locale` argument.

        ```py
        def test():
            return _("Hello, World!", _locale=Locale.french)
        ```

    Or, if you don't know the locale when you define the string, you can set `_locale` to `None`.

        ```py
        my_strings = {
            "blue": _("The sea is blue!", _locale=None),
            "red": _("Red is the color of blood!", _locale=None),
        }

        @app_command.command()
        async def color(self, inter: Interaction, color: Literal["blue", "red"]):
            await inter.response.send_message(_(my_strings[color]))  # note the use of the `_` function here
        ```

    The last special case is when your context can have an interaction in the stack, **OR** not. Then you can use the
    `_silent` argument to silent the warning message if the interaction was not found.
    This is useful for persistant view, that will be loaded at startup and when sending new views.

        ```py
        class MyView(View):
            def __init__(self):
                super().__init__()
                self.click_me.label = _("Click me!", _silent=True)

            @ui.button(custom_id="click_me")
            async def click_me(self, inter: Interaction, button: Button):
                await inter.response.send_message(_("You clicked me!"))
        ```

    Args:
        string: the string to translate.
        _locale: allow to manually set the target language.
        _silent: silent the warning message if the interaction was not found.
        _l: allow to set a max size for translated strings.

    Returns:
        The translated string according to the user's locale.
    """
    if string == "":
        return string

    if _locale is MISSING:
        stack = inspect.stack()

        inter: Interaction | None = None
        for frame_info in stack:
            inter = find((lambda _item: isinstance(_item, Interaction)), frame_info.frame.f_locals.values())
            if inter is not None:
                break

        if inter is None:
            if not _silent:
                caller = inspect.getframeinfo(inspect.stack()[1][0])
                logger.warning(
                    'i18n function cannot retrieve an interaction for the string "%s" at line %s in file %s',
                    string,
                    caller.lineno,
                    caller.filename,
                )
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
