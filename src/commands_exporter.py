from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypedDict, cast

import discord
from discord import app_commands
from typing_extensions import NotRequired

from core._config import define_config
from core.misc_command import MiscCommandsType

if TYPE_CHECKING:
    from mybot import MyBot


Features = list["Feature"]


class FeatureType(Enum):
    chat_input = "chat_input"
    context_user = "context_user"
    context_message = "context_message"
    misc = "misc"


@dataclass(kw_only=True)
class Feature:
    type: FeatureType
    name: str
    guild_only: bool
    nsfw: bool
    default_permissions: int | None
    beta: bool
    soon: bool
    description: str


@dataclass(kw_only=True)
class SlashCommand(Feature):
    type: FeatureType = FeatureType.chat_input
    parameters: list[SlashCommandParameter]


@dataclass()
class SlashCommandParameter:
    name: str
    description: str
    required: bool
    type: int


@dataclass(kw_only=True)
class ContextCommand(Feature):
    pass


@dataclass(kw_only=True)
class Misc(Feature):
    type: FeatureType = FeatureType.misc
    misc_type: MiscCommandsType


class Extras(TypedDict):
    beta: NotRequired[bool]
    description: NotRequired[str]  # if ContextMenu
    bot_required_permissions: NotRequired[list[str]]


def extract_features(mybot: MyBot) -> Features:
    features: Features = []

    for app_command in mybot.tree.get_commands():
        extras = cast(Extras, app_command.extras)

        match app_command:
            case app_commands.Command():
                feature = SlashCommand(
                    name=app_command.name,
                    guild_only=app_command.guild_only,
                    nsfw=app_command.nsfw,
                    default_permissions=app_command.default_permissions.value
                    if app_command.default_permissions
                    else None,
                    description=app_command.description,
                    parameters=[],
                    beta=extras.get("beta", False),
                    soon=extras.get("soon", False),
                )

                for parameter in app_command.parameters:
                    parameter_payload = SlashCommandParameter(
                        name=parameter.name,
                        description=parameter.description,
                        type=parameter.type.value,
                        required=parameter.required,
                    )
                    feature.parameters.append(parameter_payload)

                features.append(feature)
            case app_commands.ContextMenu():
                equiv = {
                    discord.AppCommandType.user: FeatureType.context_user,
                    discord.AppCommandType.message: FeatureType.context_message,
                }
                feature = ContextCommand(
                    type=equiv[app_command.type],
                    name=app_command.name,
                    guild_only=app_command.guild_only,
                    nsfw=app_command.nsfw,
                    default_permissions=app_command.default_permissions.value
                    if app_command.default_permissions
                    else None,
                    description=extras.get("description", ""),
                    beta=extras.get("beta", False),
                    soon=extras.get("soon", False),
                )

                features.append(feature)
            case app_commands.Group():
                # TODO : handle groups
                feature = SlashCommand(
                    name=app_command.name,
                    guild_only=app_command.guild_only,
                    nsfw=app_command.nsfw,
                    default_permissions=app_command.default_permissions.value
                    if app_command.default_permissions
                    else None,
                    description=app_command.description,
                    beta=extras.get("beta", False),
                    soon=extras.get("soon", False),
                    parameters=[],
                )
                features.append(feature)

    for misc_cmd in mybot.misc_commands():
        misc_feat = Misc(
            name=misc_cmd.name,
            description=misc_cmd.description,
            guild_only=misc_cmd.guild_only,
            default_permissions=misc_cmd.default_permissions,
            beta=misc_cmd.extras.get("beta", False),
            soon=misc_cmd.extras.get("soon", False),
            nsfw=misc_cmd.nsfw,
            misc_type=misc_cmd.type,
        )

        features.append(misc_feat)

    return features


async def export(mybot: MyBot, filename: str = "features.json") -> None:
    features: Features = extract_features(mybot)

    # TODO : fix features export to json.

    with open(filename, "w") as file:
        json.dump(features, file, indent=4)


async def main():
    mybot = MyBot(False)
    await mybot.load_extensions()

    print(extract_features(mybot))

    # await export(mybot)


if __name__ == "__main__":
    from mybot import MyBot

    define_config(EXPORT_MODE=True)

    asyncio.run(main())
