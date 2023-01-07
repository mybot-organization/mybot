from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, Sequence, cast

from discord import Embed, Message, app_commands
from discord.app_commands import locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]

from utils import ResponseType, TemporaryCache, response_constructor
from utils.i18n import _

from ._types import BatchTranslatorFunction, DetectorFunction, LanguageProtocol, Strategies, StrategiesSet
from .translator import Language, batch_translate, detect

if TYPE_CHECKING:
    from discord import Interaction, RawReactionActionEvent
    from discord.abc import MessageableChannel

    from mybot import MyBot


logger = logging.getLogger(__name__)


detect: DetectorFunction
batch_translate: BatchTranslatorFunction
Language: LanguageProtocol


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


@dataclass
class TranslationTask:
    content: str | None = None
    tr_embeds: list[EmbedTranslation] = field(default_factory=list)

    @property
    def values(self) -> list[str]:
        return ([self.content] if self.content else []) + [value for embed in self.tr_embeds for value in embed.values]

    def inject_transations(self, translation: Sequence[str]):
        i = 0
        if self.content is not None:
            self.content = translation[0]
            i += 1
        for tr_embed in self.tr_embeds:
            tr_embed.reconstruct(translation[i : i + len(tr_embed.values)])
            i += len(tr_embed.values)


class EmbedTranslation:
    def __init__(self, embed: Embed):
        self.dict_embed = embed.to_dict()
        self.deconstruct()

    def deconstruct(self):
        pointers: list[str] = []
        values: list[str] = []

        if "title" in self.dict_embed:
            pointers.append("title")
            values.append(self.dict_embed["title"])
        if "description" in self.dict_embed:
            pointers.append("description")
            values.append(self.dict_embed["description"])
        if "fields" in self.dict_embed:
            for i, field in enumerate(self.dict_embed["fields"]):
                pointers.append(f"fields.{i}.name")
                pointers.append(field["name"])
                pointers.append(f"fields.{i}.value")
                pointers.append(field["value"])
        if "author" in self.dict_embed:
            if "name" in self.dict_embed["author"]:
                pointers.append("author.name")
                values.append(self.dict_embed["author"]["name"])
        if "footer" in self.dict_embed and "text" in self.dict_embed["footer"]:
            pointers.append("footer.text")
            values.append(self.dict_embed["footer"]["text"])

        self._pointers: tuple[str, ...] = tuple(pointers)
        self._values: tuple[str, ...] = tuple(values)

    @property
    def values(self) -> tuple[str, ...]:
        return self._values

    def reconstruct(self, translations: Sequence[str]):
        for pointer, translation in zip(self._pointers, translations):
            keys = pointer.split(".")
            current: Any = self.dict_embed
            for key in keys[:-1]:
                if key.isdigit():  # for fields
                    key = int(key)
                current = current[key]
            current[keys[-1]] = translation  # to edit memory in place

    @property
    def embed(self) -> Embed:
        return Embed.from_dict(self.dict_embed)


class Translate(Cog):
    def __init__(self, bot: MyBot):
        self.bot: MyBot = bot
        self.cache: TemporaryCache[str, TranslationTask] = TemporaryCache(expire=timedelta(days=1), max_size=10_000)

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
            TranslationTask(content=text),
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
            TranslationTask(
                content=message.content or None, tr_embeds=[EmbedTranslation(embed) for embed in message.embeds[:4]]
            ),
            language,
            None,
            StrategiesSet(
                public=Strategies(pre=public_pre_strategy, send=partial(channel.send, reference=message)),
                private=Strategies(pre=private_pre_strategy, send=user.send),
            ),
            message_reference=message,
        )

    async def translate_message_ctx(self, inter: Interaction, message: Message) -> None:
        to_language = Language.from_discord_locale(inter.locale)
        if not to_language:
            return  # TODO: raise unsupported.

        await self.process(
            TranslationTask(
                content=message.content, tr_embeds=[EmbedTranslation(embed) for embed in message.embeds[:4]]
            ),
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
        translation_task: TranslationTask,
        to: LanguageProtocol,
        from_: LanguageProtocol | None,
        strategies_set: StrategiesSet,
        message_reference: Message | None = None,
    ):
        PUBLIC = True
        if PUBLIC:
            strategies = strategies_set.public
        else:
            strategies = strategies_set.private

        await strategies.pre()

        if from_ is None:
            from_ = await detect(translation_task.values[0])

        use_cache = message_reference is not None  # we cache because we can retrieve.
        if use_cache and (cached := self.cache.get(f"{message_reference.id}:{to.code}")):
            translation_task = cached
        else:
            translated_values = await batch_translate(translation_task.values, to, from_)
            translation_task.inject_transations(translated_values)

            if use_cache:
                self.cache[f"{message_reference.id}:{to.code}"] = translation_task

        head = response_constructor(
            ResponseType.success,
            _("Translate from {from_} to {to}", from_=from_.name if from_ else "auto", to=to.name, _locale=to.locale),
            author_url=message_reference.jump_url if message_reference else None,
        ).embed
        head.description = translation_task.content

        await strategies.send(embeds=[head, *[tr_embed.embed for tr_embed in translation_task.tr_embeds]])


async def setup(bot: MyBot):
    await bot.add_cog(Translate(bot))
