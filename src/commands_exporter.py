from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypedDict, cast

from discord import app_commands
from typing_extensions import NotRequired

if TYPE_CHECKING:
    from mybot import MyBot


Features = list["Feature"]


class FeatureType(Enum):
    chat_input = "chat_input"
    context_user = "context_user"
    context_message = "context_message"


@dataclass(kw_only=True)
class Feature:
    type: FeatureType
    name: str
    guild_only: bool
    nsfw: bool
    default_permissions: int | None
    beta: bool
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


class Extras(TypedDict):
    beta: NotRequired[bool]
    description: NotRequired[str]


def features_to_dict(mybot: MyBot) -> Features:
    features: Features = []

    for app_command in mybot.tree.get_commands():
        extras = cast(Extras, app_command.extras)

        if type(app_command) is app_commands.Command:
            slash_command = SlashCommand(
                name=app_command.name,
                guild_only=app_command.guild_only,
                nsfw=app_command.nsfw,
                default_permissions=app_command.default_permissions.value if app_command.default_permissions else None,
                description=app_command.description,
                parameters=[],
                beta=extras.get("beta", False),
            )

            for parameter in app_command.parameters:
                parameter_payload = SlashCommandParameter(
                    name=parameter.name,
                    description=parameter.description,
                    type=parameter.type.value,
                    required=parameter.required,
                )
                slash_command.parameters.append(parameter_payload)

            features.append(slash_command)

    return features


async def export(mybot: MyBot, filename: str = "features.json") -> None:
    features: Features = features_to_dict(mybot)
    with open(filename, "w") as file:
        json.dump(features, file, indent=4)


async def main():
    mybot = MyBot()
    await mybot.load_extensions()

    await export(mybot)


if __name__ == "__main__":
    from mybot import MyBot

    asyncio.run(main())
