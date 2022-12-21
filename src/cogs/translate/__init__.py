from __future__ import annotations
from datetime import timedelta

import logging
from functools import partial
from typing import TYPE_CHECKING, cast

from discord import Message, app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

from utils.i18n import _
from utils import TemporaryCache, response_constructor, ResponseType

from ._types import LanguageImplementation, StrategiesSet, Strategies, TranslatorFunction, DetectorFunction
from .translator import Language, translate, detect

if TYPE_CHECKING:
    from discord.abc import MessageableChannel
    from discord import Interaction, RawReactionActionEvent

    from mybot import MyBot


logger = logging.getLogger(__name__)


detect: DetectorFunction
translate: TranslatorFunction
Language: LanguageImplementation


# fmt: off
EVERY_FLAGS = (
    "🇦🇫", "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇴", "🇦🇮", "🇦🇶", "🇦🇬", "🇦🇷", "🇦🇲", "🇦🇼", "🇦🇺", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭", "🇧🇩", "🇧🇧", "🇧🇾",
    "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇹", "🇧🇴", "🇧🇶", "🇧🇦", "🇧🇼", "🇧🇻", "🇧🇷", "🇮🇴", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦", "🇨🇻",
    "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇳", "🇨🇽", "🇨🇨", "🇨🇴", "🇰🇲", "🇨🇩", "🇨🇬", "🇨🇰", "🇨🇷", "🇭🇷", "🇨🇺", "🇨🇼", "🇨🇾", "🇨🇿", "🇨🇮", "🇩🇰",
    "🇩🇯", "🇩🇲", "🇩🇴", "🇪🇨", "🇪🇬", "🇸🇻", "🇬🇶", "🇪🇷", "🇪🇪", "🇪🇹", "🇫🇰", "🇫🇴", "🇫🇯", "🇫🇮", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦", "🇬🇲",
    "🇬🇪", "🇩🇪", "🇬🇭", "🇬🇮", "🇬🇷", "🇬🇱", "🇬🇩", "🇬🇵", "🇬🇺", "🇬🇹", "🇬🇬", "🇬🇳", "🇬🇼", "🇬🇾", "🇭🇹", "🇭🇲", "🇭🇳", "🇭🇰", "🇭🇺", "🇮🇸",
    "🇮🇳", "🇮🇩", "🇮🇷", "🇮🇶", "🇮🇪", "🇮🇲", "🇮🇱", "🇮🇹", "🇯🇲", "🇯🇵", "🇯🇪", "🇯🇴", "🇰🇿", "🇰🇪", "🇰🇮", "🇽🇰", "🇰🇼", "🇰🇬", "🇱🇦", "🇱🇻",
    "🇱🇧", "🇱🇸", "🇱🇷", "🇱🇾", "🇱🇮", "🇱🇹", "🇱🇺", "🇲🇴", "🇲🇰", "🇲🇬", "🇲🇼", "🇲🇾", "🇲🇻", "🇲🇱", "🇲🇹", "🇲🇭", "🇲🇶", "🇲🇷", "🇲🇺", "🇾🇹",
    "🇲🇽", "🇫🇲", "🇲🇩", "🇲🇨", "🇲🇳", "🇲🇪", "🇲🇸", "🇲🇦", "🇲🇿", "🇲🇲", "🇳🇦", "🇳🇷", "🇳🇵", "🇳🇱", "🇳🇨", "🇳🇿", "🇳🇮", "🇳🇪", "🇳🇬", "🇳🇺",
    "🇳🇫", "🇰🇵", "🇲🇵", "🇳🇴", "🇴🇲", "🇵🇰", "🇵🇼", "🇵🇸", "🇵🇦", "🇵🇬", "🇵🇾", "🇵🇪", "🇵🇭", "🇵🇳", "🇵🇱", "🇵🇹", "🇵🇷", "🇶🇦", "🇷🇴", "🇷🇺",
    "🇷🇼", "🇷🇪", "🇧🇱", "🇸🇭", "🇰🇳", "🇱🇨", "🇲🇫", "🇵🇲", "🇻🇨", "🇼🇸", "🇸🇲", "🇸🇹", "🇸🇦", "🇸🇳", "🇷🇸", "🇸🇨", "🇸🇱", "🇸🇬", "🇸🇽", "🇸🇰",
    "🇸🇮", "🇸🇧", "🇸🇴", "🇿🇦", "🇬🇸", "🇰🇷", "🇸🇸", "🇪🇸", "🇱🇰", "🇸🇩", "🇸🇷", "🇸🇯", "🇸🇿", "🇸🇪", "🇨🇭", "🇸🇾", "🇹🇼", "🇹🇯", "🇹🇿", "🇹🇭",
    "🇹🇱", "🇹🇬", "🇹🇰", "🇹🇴", "🇹🇹", "🇹🇳", "🇹🇷", "🇹🇲", "🇹🇨", "🇹🇻", "🇺🇬", "🇺🇦", "🇦🇪", "🇬🇧", "🇺🇸", "🇺🇲", "🇺🇾", "🇺🇿", "🇻🇺", "🇻🇦",
    "🇻🇪", "🇻🇳", "🇻🇬", "🇻🇮", "🇼🇫", "🇪🇭", "🇾🇪", "🇿🇲", "🇿🇼", "🇦🇽"
)
# fmt: on


class Translate(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot
        self.cache: TemporaryCache[str, str] = TemporaryCache(expire=timedelta(days=1), max_size=10_000)

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
            StrategiesSet(
                public=Strategies(pre=inter.response.defer, send=inter.followup.send),
                private=Strategies(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send),
            ),
        )

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        emote = payload.emoji.name

        if emote not in EVERY_FLAGS:
            return

        user = await self.bot.getch_user(payload.user_id)
        if not user or user.bot:
            return

        channel = await self.bot.getch_channel(payload.channel_id)
        if channel is None:
            return
        if TYPE_CHECKING:
            channel = cast(MessageableChannel, channel)

        message = await channel.fetch_message(payload.message_id)

        language = Language.from_emote(emote)
        if not language:
            raise Exception()  # TODO: unsupported

        async def public_pre_strategy():
            await channel.typing()

        async def private_pre_strategy():
            await user.typing()

        await self.process(
            text=message.content,
            to=language,
            from_=None,
            strategies_set=StrategiesSet(
                public=Strategies(pre=public_pre_strategy, send=partial(channel.send, reference=message)),
                private=Strategies(pre=private_pre_strategy, send=user.send),
            ),
            message_reference=message,
        )

    # @app_commands.context_menu(name="Translate")
    async def translate_message_ctx(self, inter: Interaction, message: Message) -> None:
        to_language = Language.from_discord_locale(inter.locale)
        if not to_language:
            return  # TODO: raise unsupported.

        await self.process(
            message.content,
            to_language,
            None,
            StrategiesSet(
                public=Strategies(pre=inter.response.defer, send=inter.followup.send),
                private=Strategies(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send),
            ),
            message_reference=message,
        )

    async def process(
        self,
        text: str,
        to: LanguageImplementation,
        from_: LanguageImplementation | None,
        strategies_set: StrategiesSet,
        message_reference: Message | None = None,
    ):
        PUBLIC = False  # TODO: db
        if PUBLIC:
            strategies = strategies_set.public
        else:
            strategies = strategies_set.private

        await strategies.pre()

        if from_ is None:
            from_ = await detect(text)

        if message_reference is not None:
            cached = self.cache.get(f"{message_reference.id}:{to.code}")

            if cached is not None:
                translated = cached
            else:
                translated = await translate(text, to, from_)
                self.cache.set(f"{message_reference.id}:{to.code}", translated)
        else:
            translated = await translate(text, to, from_)

        head = response_constructor(
            ResponseType.success,
            _("Translate from {from_} to {to}", from_=from_.name if from_ else "auto", to=to.name, _locale=to.locale),
            author_url=message_reference.jump_url if message_reference else None,
        ).embed
        head.description = translated
        # body = Embed(description=translated)
        await strategies.send(embeds=[head])


async def setup(bot: MyBot):
    await bot.add_cog(Translate(bot))
