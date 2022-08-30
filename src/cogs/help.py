from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands, ui
from discord.app_commands import Choice, locale_str as __
from discord.ext.commands import Cog  # pyright: ignore[reportMissingTypeStubs]
from discord.utils import get
from typing_extensions import Self

from commands_exporter import FeatureType, SlashCommand, features_to_dict
from utils import ResponseType, response_constructor
from utils.constants import Emojis
from utils.i18n import _

if TYPE_CHECKING:
    from discord import Embed, Interaction

    from commands_exporter import Feature
    from mybot import MyBot


logger = logging.getLogger(__name__)

friendly_commands_types = {
    FeatureType.chat_input: _("chat input", _locale=None),  # Allow xgettext to retrieve this strings
    FeatureType.context_message: _("message context", _locale=None),
    FeatureType.context_user: _("user context", _locale=None),
}


class Help(Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

        self.bot.loop.create_task(self.load_features_info())

    async def load_features_info(self):
        if not self.bot.is_ready():
            await self.bot.wait_for("ready")

        self.features_infos = features_to_dict(self.bot)

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

        await inter.response.send_message(embed=embed, view=view)

    @_help.autocomplete("feature_identifier")
    async def feature_identifier_autocompleter(self, inter: Interaction, current: str) -> list[Choice[str]]:
        return sorted(
            [
                Choice(
                    name=f"{feature.name} [{_(friendly_commands_types[feature.type])}]",
                    value=f"{feature.type.value}.{feature.name}",
                )
                for feature in self.features_infos
                if feature.name.startswith(current) or current in feature.name
            ],
            key=lambda choice: (choice.name.startswith(current), choice.name),
        )

    def general_embed(self) -> Embed:
        beta = Emojis.beta_1 + Emojis.beta_2

        embed = response_constructor(ResponseType.info, _("Commands of MyBot"))["embed"]
        description = ""

        for feature in self.features_infos:  # TODO: check for feature type
            app_command = get(self.bot.app_commands, name=feature.name, type=discord.AppCommandType.chat_input)
            if app_command is None:
                logger.warning(f"Feature {feature.name} didn't get its app_command for some reason.")
                continue
            description += f"</{feature.name}:{app_command.id}>\n{_(feature.description)} {beta * feature.beta}\n"

        embed.add_field(name=_("Chat input commands"), value=description)
        return embed

    def feature_embed(self, feature: Feature) -> Embed:
        embed = response_constructor(
            ResponseType.info, message=_("Help about {} [{}]", feature.name, _(friendly_commands_types[feature.type]))
        )["embed"]
        embed.description = _(feature.description)

        if isinstance(feature, SlashCommand):
            pass
            # field_value = "" if feature.parameters else _("No parameters")

            # for parameter in feature.parameters:
            #     field_value += f"`{parameter.name}: {parameter.type}channel` ({_('required') if parameter.required else ('optional')})\n{_(parameter.description)}\n"

            # embed.add_field(name=_("Command parameters"), value=field_value)

        return embed

    def retrieve_feature_from_identifier(self, feature_identifier: str) -> Feature | None:
        type_, name = feature_identifier.split(".")
        return get(self.features_infos, name=name, type=FeatureType(type_))


class HelpView(ui.View):
    def __init__(self, cog: Help):
        super().__init__()
        self.cog = cog

        for feature in self.cog.features_infos:
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

    @ui.select()
    async def select_feature(self, inter: Interaction, select: ui.Select[Self]):
        feature_identifier = select.values[0]
        feature = cast("Feature", self.cog.retrieve_feature_from_identifier(feature_identifier))
        self.set_default(feature_identifier)

        await inter.response.edit_message(embed=self.cog.feature_embed(feature), view=self)


async def setup(bot: MyBot):
    await bot.add_cog(Help(bot))
