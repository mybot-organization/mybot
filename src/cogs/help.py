from __future__ import annotations

import logging
from collections import OrderedDict
from typing import TYPE_CHECKING, Iterable, Self, Sequence, cast

import discord
from discord import app_commands, ui
from discord.app_commands import Choice, locale_str as __
from discord.utils import get

from commands_exporter import ContextCommand, FeatureType, Misc, MiscCommandsType, SlashCommand
from core import ExtendedCog, ResponseType, response_constructor
from core.constants import Emojis
from core.i18n import _
from core.utils import splitter

if TYPE_CHECKING:
    from discord import Embed, Interaction

    from commands_exporter import Feature
    from mybot import MyBot


logger = logging.getLogger(__name__)

friendly_commands_types = {
    FeatureType.CHAT_INPUT: _("slash command", _locale=None),
    FeatureType.CONTEXT_MESSAGE: _("message context", _locale=None),
    FeatureType.CONTEXT_USER: _("user context", _locale=None),
    FeatureType.MISC: _("miscellaneous", _locale=None),
}


class Help(ExtendedCog):
    @app_commands.command(name=__("help"), description=__("Get help about the bot."), extras={"beta": True})
    @app_commands.rename(feature_identifier=__("feature"))
    async def _help(self, inter: Interaction, feature_identifier: str | None = None):
        view = HelpView(self)

        if feature_identifier:
            feature = self.retrieve_feature_from_identifier(feature_identifier)
            if feature is not None:
                view.set_default(feature_identifier)
                embed = self.feature_embed(feature)
            else:
                embed = self.general_embed()
        else:
            embed = self.general_embed()

        await inter.response.send_message(embed=embed)  # , view=view)

    @_help.autocomplete("feature_identifier")
    async def feature_identifier_autocompleter(self, inter: Interaction, current: str) -> list[Choice[str]]:
        return sorted(
            [
                Choice(
                    name=f"{feature.name} [{_(friendly_commands_types[feature.type])}]",
                    value=f"{feature.type.value}.{feature.name}",
                )
                for feature in self.bot.features_infos
                if feature.name.startswith(current) or current in feature.name
            ],
            key=lambda choice: (choice.name.startswith(current), choice.name),
        )

    def general_embed(self) -> Embed:
        embed = response_constructor(ResponseType.info, _("Commands of MyBot"))["embed"]

        feature_types_ui = OrderedDict(
            (
                (FeatureType.CHAT_INPUT, _("Slash commands")),
                (FeatureType.CONTEXT_MESSAGE, _("Context commands")),
                (FeatureType.MISC, _("Miscellaneous features")),
            )
        )
        description: dict[FeatureType, list[str]] = {key: [] for key in feature_types_ui}

        def set_tags(feature: Feature) -> str:
            tags: list[str] = []

            beta = f"[{Emojis.beta_1 + Emojis.beta_2}](https://google.com/)"
            soon = f"[{Emojis.soon_1 + Emojis.soon_2}](https://google.com/)"

            if feature.beta:
                tags.append(beta)
            if feature.soon:
                tags.append(soon)

            return " ".join(tags)

        for feature in self.bot.features_infos:
            match feature:
                case SlashCommand():
                    app_command = get(self.bot.app_commands, name=feature.name, type=discord.AppCommandType.chat_input)
                    if app_command is None:
                        logger.warning("Feature %s didn't get its app_command for some reason.", feature.name)
                        continue

                    if not feature.sub_commands:
                        description[feature.type].insert(
                            0,
                            f"{Emojis.slash_command} {app_command.mention} {set_tags(feature)}\n"
                            f"{_(feature.description)}",
                        )
                    else:
                        description[feature.type].append(
                            f"{Emojis.slash_command} `/{feature.name}` {set_tags(feature)}\n{_(feature.description)}"
                        )
                case ContextCommand():
                    prefix = {
                        FeatureType.CONTEXT_MESSAGE: Emojis.message_context,
                    }
                    description[FeatureType.CONTEXT_MESSAGE].append(
                        f"{prefix[feature.type]} `{_(feature.name).lower()}` {set_tags(feature)}\n"
                        f"{_(feature.description)}"
                    )

                case Misc():
                    prefix = {
                        MiscCommandsType.MESSAGE: Emojis.misc_command_text,
                        MiscCommandsType.REACTION: Emojis.misc_command_reaction,
                    }

                    description[feature.type].append(
                        f"[{prefix[feature.misc_type]}](https://google.com) `{_(feature.name).lower()}` "
                        f"{set_tags(feature)}\n{_(feature.description)}"
                    )
                case _:
                    pass  # should never happen

        for feature_type, feature_type_ui in feature_types_ui.items():
            if not description[feature_type]:
                continue
            chunks: Iterable[Sequence[str]] = splitter(description[feature_type], 2)
            empty: list[str] = []  # type purpose only
            embed.add_field(name=feature_type_ui, value="\n".join(next(chunks, empty)), inline=True)
            embed.add_field(name="\u200b", value="\n".join(next(chunks, empty)), inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        return embed

    def feature_embed(self, feature: Feature) -> Embed:
        embed = response_constructor(
            ResponseType.info, message=_("Help about {} [{}]", feature.name, _(friendly_commands_types[feature.type]))
        )["embed"]
        embed.description = _(feature.description)

        return embed

    def retrieve_feature_from_identifier(self, feature_identifier: str) -> Feature | None:
        type_, name = feature_identifier.split(".")
        return get(self.bot.features_infos, name=name, type=FeatureType(type_))


class HelpView(ui.View):
    def __init__(self, cog: Help):
        super().__init__()
        self.cog = cog

        for feature in self.cog.bot.features_infos:
            self.select_feature.options.append(
                discord.SelectOption(
                    label=f"{feature.name} [{_(friendly_commands_types[feature.type])}]",
                    value=f"{feature.type.value}.{feature.name}",
                )
            )

    def set_default(self, feature_identifier: str) -> None:
        for option in self.select_feature.options:
            if option.value == feature_identifier:
                option.default = True
            else:
                option.default = False

    @ui.select(cls=ui.Select[Self])
    async def select_feature(self, inter: Interaction, select: ui.Select[Self]):
        feature_identifier = select.values[0]
        feature = cast("Feature", self.cog.retrieve_feature_from_identifier(feature_identifier))
        self.set_default(feature_identifier)

        await inter.response.edit_message(embed=self.cog.feature_embed(feature), view=self)


async def setup(bot: MyBot):
    await bot.add_cog(Help(bot))
