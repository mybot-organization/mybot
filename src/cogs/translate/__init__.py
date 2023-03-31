from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, NamedTuple, Sequence, cast

import discord
from discord import Embed, Message, app_commands, ui
from discord.app_commands import locale_str as __

from core import ResponseType, SpecialCog, TemporaryCache, misc_command, response_constructor
from core.checkers import is_activated, is_user_authorized, misc_check, misc_cmd_bot_required_permissions
from core.errors import BadArgument, NonSpecificError
from core.i18n import _

from .languages import Language

if TYPE_CHECKING:
    from discord import Interaction, RawReactionActionEvent
    from discord.abc import MessageableChannel

    from mybot import MyBot

    from ._types import PreSendStrategy, SendStrategy
    from .translator_abc import TranslatorAdapter


logger = logging.getLogger(__name__)


# fmt: off
EVERY_FLAGS = (
    "🇦🇫", "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇴", "🇦🇮", "🇦🇶", "🇦🇬", "🇦🇷", "🇦🇲", "🇦🇼", "🇦🇺", "🇦🇹",
    "🇦🇿", "🇧🇸", "🇧🇭", "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇹", "🇧🇴", "🇧🇶", "🇧🇦",
    "🇧🇼", "🇧🇻", "🇧🇷", "🇮🇴", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦", "🇨🇻", "🇰🇾", "🇨🇫",
    "🇹🇩", "🇨🇱", "🇨🇳", "🇨🇽", "🇨🇨", "🇨🇴", "🇰🇲", "🇨🇩", "🇨🇬", "🇨🇰", "🇨🇷", "🇭🇷", "🇨🇺", "🇨🇼",
    "🇨🇾", "🇨🇿", "🇨🇮", "🇩🇰", "🇩🇯", "🇩🇲", "🇩🇴", "🇪🇨", "🇪🇬", "🇸🇻", "🇬🇶", "🇪🇷", "🇪🇪", "🇪🇹",
    "🇫🇰", "🇫🇴", "🇫🇯", "🇫🇮", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦", "🇬🇲", "🇬🇪", "🇩🇪", "🇬🇭", "🇬🇮",
    "🇬🇷", "🇬🇱", "🇬🇩", "🇬🇵", "🇬🇺", "🇬🇹", "🇬🇬", "🇬🇳", "🇬🇼", "🇬🇾", "🇭🇹", "🇭🇲", "🇭🇳", "🇭🇰",
    "🇭🇺", "🇮🇸", "🇮🇳", "🇮🇩", "🇮🇷", "🇮🇶", "🇮🇪", "🇮🇲", "🇮🇱", "🇮🇹", "🇯🇲", "🇯🇵", "🇯🇪", "🇯🇴",
    "🇰🇿", "🇰🇪", "🇰🇮", "🇽🇰", "🇰🇼", "🇰🇬", "🇱🇦", "🇱🇻", "🇱🇧", "🇱🇸", "🇱🇷", "🇱🇾", "🇱🇮", "🇱🇹",
    "🇱🇺", "🇲🇴", "🇲🇰", "🇲🇬", "🇲🇼", "🇲🇾", "🇲🇻", "🇲🇱", "🇲🇹", "🇲🇭", "🇲🇶", "🇲🇷", "🇲🇺", "🇾🇹",
    "🇲🇽", "🇫🇲", "🇲🇩", "🇲🇨", "🇲🇳", "🇲🇪", "🇲🇸", "🇲🇦", "🇲🇿", "🇲🇲", "🇳🇦", "🇳🇷", "🇳🇵", "🇳🇱",
    "🇳🇨", "🇳🇿", "🇳🇮", "🇳🇪", "🇳🇬", "🇳🇺", "🇳🇫", "🇰🇵", "🇲🇵", "🇳🇴", "🇴🇲", "🇵🇰", "🇵🇼", "🇵🇸",
    "🇵🇦", "🇵🇬", "🇵🇾", "🇵🇪", "🇵🇭", "🇵🇳", "🇵🇱", "🇵🇹", "🇵🇷", "🇶🇦", "🇷🇴", "🇷🇺", "🇷🇼", "🇷🇪",
    "🇧🇱", "🇸🇭", "🇰🇳", "🇱🇨", "🇲🇫", "🇵🇲", "🇻🇨", "🇼🇸", "🇸🇲", "🇸🇹", "🇸🇦", "🇸🇳", "🇷🇸", "🇸🇨",
    "🇸🇱", "🇸🇬", "🇸🇽", "🇸🇰", "🇸🇮", "🇸🇧", "🇸🇴", "🇿🇦", "🇬🇸", "🇰🇷", "🇸🇸", "🇪🇸", "🇱🇰", "🇸🇩",
    "🇸🇷", "🇸🇯", "🇸🇿", "🇸🇪", "🇨🇭", "🇸🇾", "🇹🇼", "🇹🇯", "🇹🇿", "🇹🇭", "🇹🇱", "🇹🇬", "🇹🇰", "🇹🇴",
    "🇹🇹", "🇹🇳", "🇹🇷", "🇹🇲", "🇹🇨", "🇹🇻", "🇺🇬", "🇺🇦", "🇦🇪", "🇬🇧", "🇺🇸", "🇺🇲", "🇺🇾", "🇺🇿",
    "🇻🇺", "🇻🇦", "🇻🇪", "🇻🇳", "🇻🇬", "🇻🇮", "🇼🇫", "🇪🇭", "🇾🇪", "🇿🇲", "🇿🇼", "🇦🇽"
)
# fmt: on


class Strategies(NamedTuple):
    pre: PreSendStrategy
    send: SendStrategy


@dataclass
class TranslationTask:
    content: str | None = None
    tr_embeds: list[EmbedTranslation] = field(default_factory=list)

    @property
    def values(self) -> list[str]:
        return ([self.content] if self.content else []) + [value for embed in self.tr_embeds for value in embed.values]

    def inject_translations(self, translation: Sequence[str]):
        i = 0
        if self.content is not None:
            self.content = translation[0]
            i += 1
        for tr_embed in self.tr_embeds:
            tr_embed.reconstruct(translation[i : i + len(tr_embed.values)])  # noqa: E203
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
            for i, embed_field in enumerate(self.dict_embed["fields"]):
                pointers.append(f"fields.{i}.name")
                values.append(embed_field["name"])
                pointers.append(f"fields.{i}.value")
                values.append(embed_field["value"])
        if "author" in self.dict_embed and "name" in self.dict_embed["author"]:
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


class TempUsage:
    def __init__(self):
        self.cache: dict[datetime, list[int]] = {}

    def clean(self):
        for k in list(self.cache.keys()):
            if k < datetime.now() - timedelta(hours=12):
                del self.cache[k]

    def count_usage(self, id: int):
        self.clean()
        return sum(v.count(id) for v in self.cache.values())

    def add_usage(self, id: int):
        self.clean()
        key = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.cache.setdefault(key, [])
        self.cache[key].append(id)


class Translate(SpecialCog["MyBot"]):
    def __init__(self, bot: MyBot):
        super().__init__(bot)
        self.cache: TemporaryCache[str, TranslationTask] = TemporaryCache(expire=timedelta(days=1), max_size=10_000)
        self.tmp_user_usage = TempUsage()

        self.translators: list[TranslatorAdapter] = []
        for adapter in self.bot.config.TRANSLATOR_SERVICES.split(","):
            adapter_module = importlib.import_module(f".adapters.{adapter}", __name__)
            self.translators.append(adapter_module.get_translator()())

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name=__("Translate"),
                callback=self.translate_message_ctx,
                extras={
                    "beta": True,
                    "description": _("Translate a message based on your discord settings.", _locale=None),
                },
            )
        )

    async def public_translations(self, guild_id: int | None):
        if guild_id is None:  # we are in private channels, IG
            return True
        guild_db = await self.bot.get_guild_db(guild_id)
        return guild_db.translations_are_public

    @app_commands.command(
        name=__("translate"),
        description=__("Translate text in a selection of languages."),
        extras={"beta": True},
    )
    async def translate_slash(self, inter: Interaction, to: str, text: str, from_: str | None = None) -> None:
        available_languages = await self.translators[0].available_languages()
        to_language = available_languages.from_code(to)
        if to_language is None:
            raise BadArgument(_("The language you provided is not supported."))

        if from_ is not None:
            from_language = available_languages.from_code(from_)
            if from_language is None:
                raise BadArgument(_(f"The language you provided under the argument `from_` is not supported : {from_}"))
        else:
            from_language = None

        if await self.public_translations(inter.guild_id):
            strategies = Strategies(pre=inter.response.defer, send=inter.followup.send)
        else:
            strategies = Strategies(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send)

        await self.process(
            inter.user.id,
            TranslationTask(content=text),
            to_language,
            from_language,
            send_strategies=strategies,
        )

    @translate_slash.autocomplete("to")
    @translate_slash.autocomplete("from_")
    async def translate_slash_autocomplete_to(self, inter: Interaction, current: str) -> list[app_commands.Choice[str]]:
        available_languages = await self.translators[0].available_languages()

        return [
            app_commands.Choice(name=lang.name, value=lang.lang_code)
            for lang in available_languages
            if lang.name.startswith(current)
        ][:25]

    async def translate_misc_condition(self, payload: RawReactionActionEvent) -> bool:
        available_languages = await self.translators[0].available_languages()
        return (
            payload.emoji.is_unicode_emoji()
            and payload.emoji.name in EVERY_FLAGS
            and available_languages.from_emote(payload.emoji.name) is not None
        )

    @misc_command(
        "translate",
        description=_("Translate text in the language corresponding on the flag you add.", _locale=None),
        listener_name="raw_reaction_add",
        extras={"beta": True},
        trigger_condition=translate_misc_condition,
    )
    @misc_cmd_bot_required_permissions(send_messages=True, embed_links=True)
    @misc_check(is_activated)
    @misc_check(is_user_authorized)
    async def translate_misc_command(self, payload: RawReactionActionEvent):
        user = await self.bot.getch_user(payload.user_id)
        if not user or user.bot:  # TODO(airo.pi_): automatically ignore bots
            return

        channel = await self.bot.getch_channel(payload.channel_id)
        if channel is None:
            return
        if TYPE_CHECKING:
            channel = cast(MessageableChannel, channel)

        available_languages = await self.translators[0].available_languages()
        language = available_languages.from_emote(payload.emoji.name)
        if language is None:
            raise ValueError(_("The language you asked for is not supported."))

        message = await channel.fetch_message(payload.message_id)

        async def public_pre_strategy():
            await channel.typing()

        async def private_pre_strategy():
            await user.typing()

        if await self.public_translations(payload.guild_id):
            strategies = Strategies(pre=public_pre_strategy, send=partial(channel.send, reference=message))
        else:
            strategies = Strategies(pre=private_pre_strategy, send=user.send)

        await self.process(
            payload.user_id,
            TranslationTask(
                content=message.content or None, tr_embeds=[EmbedTranslation(embed) for embed in message.embeds[:4]]
            ),
            language,
            None,
            send_strategies=strategies,
            message_reference=message,
        )

    # command definition is in Translate.__init__ because of dpy limitation!
    async def translate_message_ctx(self, inter: Interaction, message: Message) -> None:
        available_languages = await self.translators[0].available_languages()
        to_language = available_languages.from_locale(inter.locale)
        if not to_language:
            raise NonSpecificError(_("Your locale is not supported."))

        if await self.public_translations(inter.guild_id):
            strategies = Strategies(pre=inter.response.defer, send=inter.followup.send)
        else:
            strategies = Strategies(pre=partial(inter.response.defer, ephemeral=True), send=inter.followup.send)

        await self.process(
            inter.user.id,
            TranslationTask(
                content=message.content, tr_embeds=[EmbedTranslation(embed) for embed in message.embeds[:4]]
            ),
            to_language,
            None,
            send_strategies=strategies,
            message_reference=message,
        )

    async def check_user_quotas(self, user_id: int, strategy: SendStrategy) -> bool:
        if self.tmp_user_usage.count_usage(user_id) < 10:
            return True
        if await self.bot.get_topgg_vote(user_id):
            return True

        view = ui.View().add_item(
            ui.Button(
                style=discord.ButtonStyle.url,
                label=_("Vote for the bot", _locale=None),
                url=f"https://top.gg/bot/{self.bot.config.BOT_ID}/vote",
            )
        )
        await strategy(
            **response_constructor(
                ResponseType.warning,
                _(
                    "You have reached the maximum number of translations per day."
                    "Vote for the bot to remove this limit !",
                    _locale=None,
                ),
            ),
            view=view,
        )

        return False

    async def process(
        self,
        user_id: int,
        translation_task: TranslationTask,
        to: Language,
        from_: Language | None,
        send_strategies: Strategies,
        message_reference: Message | None = None,
    ):
        translator = self.translators[0]
        if not await self.check_user_quotas(user_id, send_strategies.send):
            return
        self.tmp_user_usage.add_usage(user_id)
        await send_strategies.pre()

        if from_ is None:
            from_ = await translator.detect(translation_task.values[0])

        use_cache = message_reference is not None  # we cache because we can retrieve.
        if use_cache and (cached := self.cache.get(f"{message_reference.id}:{to.lang_code}")):
            translation_task = cached
        else:
            translated_values = await translator.batch_translate(translation_task.values, to, from_)
            translation_task.inject_translations(translated_values)

            if use_cache:
                self.cache[f"{message_reference.id}:{to.lang_code}"] = translation_task

        head = response_constructor(
            ResponseType.success,
            _(
                "Translate from {from_} to {to}",
                from_=from_.name if from_ else "auto",
                to=to.name,
                _locale=to.discord_locale,
            ),
            author_url=message_reference.jump_url if message_reference else None,
        ).embed
        head.description = translation_task.content

        await send_strategies.send(embeds=[head, *[tr_embed.embed for tr_embed in translation_task.tr_embeds]])


async def setup(bot: MyBot):
    await bot.add_cog(Translate(bot))
