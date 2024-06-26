from __future__ import annotations

import importlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any, NamedTuple, cast

import discord
from discord import Embed, Message, app_commands, ui
from discord.app_commands import locale_str as __

from core import ExtendedCog, MiscCommandContext, ResponseType, TemporaryCache, db, misc_command, response_constructor
from core.checkers import bot_required_permissions, check, is_activated_predicate, is_user_authorized_predicate
from core.constants import EmbedsCharLimits
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
        return ([self.content] if self.content else []) + [
            value for embed in self.tr_embeds for value in embed.flattened.values()
        ]

    def inject_translations(self, translation: Sequence[str]):
        i = 0
        if self.content:
            self.content = translation[0][: EmbedsCharLimits.DESCRIPTION.value - 1]
            i += 1
        for tr_embed in self.tr_embeds:
            tr_embed.reconstruct(translation[i : i + len(tr_embed)])
            i += len(tr_embed)


class EmbedTranslation:
    def __init__(self, embed: Embed):
        self.dict_embed = embed.to_dict()
        self._flattened = self.flat()

    def __len__(self):
        return len(self._flattened)

    def flat(self) -> dict[str, str]:
        """Flat then embed to a key-value dict of strings.

        Nested keys are separated by a dot. List are indexed.
        For example:
        ```py
        {
            "title": "Hello",
            "fields": [
                {"name": "Field 1", "value": "Value 1"},
                {"name": "Field 2", "value": "Value 2"},
            ],
        }
        ```
        Gives:
        ```py
        {
            "title": "Hello",
            "fields.0.name": "Field 1",
            "fields.0.value": "Value 1",
            "fields.1.name": "Field 2",
            "fields.1.value": "Value 2",
        }
        ```

        We use dict only because they are ordered now.
        Key that are not destined to be translated are not included.
        """
        result = dict[str, str]()

        if "title" in self.dict_embed:
            result["title"] = self.dict_embed["title"]
        if "description" in self.dict_embed:
            result["description"] = self.dict_embed["description"]
        if "fields" in self.dict_embed:
            for i, embed_field in enumerate(self.dict_embed["fields"]):
                result[f"fields.{i}.name"] = embed_field["name"]
                result[f"fields.{i}.value"] = embed_field["value"]
        if "author" in self.dict_embed and "name" in self.dict_embed["author"]:
            result["author.name"] = self.dict_embed["author"]["name"]
        if "footer" in self.dict_embed and "text" in self.dict_embed["footer"]:
            result["footer.text"] = self.dict_embed["footer"]["text"]

        return result

    @property
    def flattened(self) -> dict[str, str]:
        return self._flattened

    def reconstruct(self, translations: Sequence[str]):
        for pointer, translation in zip(self.flattened.keys(), translations):
            keys = pointer.split(".")
            obj: Any = self.dict_embed
            char_lim_key: list[str] = []
            for key in keys[:-1]:
                if key.isdigit():  # list index
                    key = int(key)
                else:
                    char_lim_key.append(key)
                obj = obj[key]

            try:
                limit = EmbedsCharLimits["_".join([*char_lim_key, keys[-1]]).upper()]
            except KeyError:
                limit = None

            if limit and limit.value < len(translation):
                obj[keys[-1]] = translation[: limit.value - 1] + "…"
            else:
                obj[keys[-1]] = translation

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


class Translate(ExtendedCog):
    def __init__(self, bot: MyBot):
        super().__init__(bot)
        self.cache: TemporaryCache[str, TranslationTask] = TemporaryCache(expire=timedelta(days=1), max_size=10_000)
        self.tmp_user_usage = TempUsage()

        self.translators: list[TranslatorAdapter] = []
        for adapter in self.bot.config.translator_services:
            adapter_module = importlib.import_module(f".adapters.{adapter}", __name__)
            self.translators.append(adapter_module.get_translator()())

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name=__("Translate"),
                callback=self.translate_message_ctx,
                extras={
                    "beta": True,
                    "description": _("Translate a message with your account language settings.", _locale=None),
                },
            )
        )

    async def cog_unload(self) -> None:
        for translator in self.translators:
            await translator.close()

    async def public_translations(self, guild_id: int | None):
        if guild_id is None:  # we are in private channels, IG
            return True
        async with self.bot.async_session.begin() as session:
            guild_db = await self.bot.get_or_create_db(session, db.GuildDB, guild_id=guild_id)
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
                raise BadArgument(
                    _("The language you provided under the argument `from_` is not supported : {}", from_)
                )
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
    @bot_required_permissions(send_messages=True, embed_links=True)
    @check(is_activated_predicate)
    @check(is_user_authorized_predicate)
    async def translate_misc_command(self, ctx: MiscCommandContext[MyBot], payload: RawReactionActionEvent):
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
            await ctx.user.typing()

        if await self.public_translations(payload.guild_id):
            strategies = Strategies(pre=public_pre_strategy, send=partial(channel.send, reference=message))
        else:
            strategies = Strategies(pre=private_pre_strategy, send=ctx.user.send)

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
                url=f"https://top.gg/bot/{self.bot.user.id}/vote",  # pyright: ignore[reportOptionalMemberAccess]
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

        use_cache = message_reference is not None
        if use_cache and (cached := self.cache.get(f"{message_reference.id}:{to.lang_code}")):
            translation_task = cached
        else:
            translated_values = await translator.batch_translate(translation_task.values, to, from_)
            translation_task.inject_translations(tuple(self.clean_translation(t) for t in translated_values))

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

    def clean_translation(self, translation: str) -> str:
        """This function will try to clean the translation by removing some spaces etc..."""
        translation = translation.replace("\xa0:", ":")
        return translation


async def setup(bot: MyBot):
    await bot.add_cog(Translate(bot))
