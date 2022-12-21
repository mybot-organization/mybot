from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any

from discord import Message, app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

from utils.i18n import _

from ._types import LanguageImplementation, Strategies, StrategyNatures, TranslatorFunction
from .translator import Language, translate  # type: ignore # TODO: ask

if TYPE_CHECKING:
    from discord import Interaction, RawReactionActionEvent

    from mybot import MyBot


logger = logging.getLogger(__name__)


translate: TranslatorFunction
Language: LanguageImplementation


class Translate(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot

        self.bot.tree.add_command(app_commands.ContextMenu(name=__("Translate"), callback=self.translate_message_ctx))

    @app_commands.command(name=__("translate"), description=__("Translate text in a selection of languages."))
    async def translate_slash(self, inter: Interaction, to: str, text: str, from_: str | None = None) -> None:
        to_language = Language.from_code(to)
        if to_language is None:
            return

        if from_ is not None:
            from_language = Language.from_code(from_)
        else:
            from_language = None

        await self.process(
            text,
            to_language,
            from_language,
            Strategies(
                public=StrategyNatures(pre=inter.response.defer, send=inter.followup.send),
                private=StrategyNatures(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send),
            ),
        )

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        pass

    async def translate_to_message_ctx(self, inter: Interaction, message: Message) -> None:
        pass

    # @app_commands.context_menu(name="Translate")
    async def translate_message_ctx(self, inter: Interaction, message: Message) -> None:
        to_language = Language.from_discord_locale(inter.locale)
        if not to_language:
            return  # TODO: raise unsupported.

        await self.process(
            message.content,
            to_language,
            None,
            Strategies(
                public=StrategyNatures(pre=inter.response.defer, send=inter.followup.send),
                private=StrategyNatures(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send),
            ),
        )

    async def process(
        self, text: str, to: LanguageImplementation, from_: LanguageImplementation | None, strategies: Strategies
    ):
        PUBLIC = True  # TODO: db
        if PUBLIC:
            strategy = strategies.public
        else:
            strategy = strategies.private

        await strategy.pre()

        translated = await translate(text, to, from_)

        await strategy.send(content=translated)


async def setup(bot: MyBot):
    await bot.add_cog(Translate(bot))
