from __future__ import annotations

import asyncio
import json
from typing import Literal, TypedDict

from discord import app_commands

from mybot import MyBot


class Features(TypedDict):
    slash_commands: list[SlashCommand]
    context_commands: list[ContextCommand]


class Command(TypedDict):
    name: str
    guild_only: bool
    nsfw: bool
    default_permissions: int | None


class SlashCommand(Command):
    description: str
    parameters: list[SlashCommandParameter]


class SlashCommandParameter(TypedDict):
    name: str
    description: str
    required: bool
    type: int


class ContextCommand(Command):
    type: Literal["user", "message"]


async def features_to_dict() -> Features:
    mybot = MyBot()
    features = Features(slash_commands=[], context_commands=[])

    await mybot.load_extensions()

    for app_command in mybot.tree.get_commands():
        if type(app_command) is app_commands.Command:
            slash_command = SlashCommand(
                name=app_command.name,
                guild_only=app_command.guild_only,
                nsfw=app_command.nsfw,
                default_permissions=app_command.default_permissions.value if app_command.default_permissions else None,
                description=app_command.description,
                parameters=[],
            )

            for parameter in app_command.parameters:
                parameter_payload = SlashCommandParameter(
                    name=parameter.name,
                    description=parameter.description,
                    type=parameter.type.value,
                    required=parameter.required,
                )
                slash_command["parameters"].append(parameter_payload)

            features["slash_commands"].append(slash_command)

    return features


async def export(filename: str = "features.json") -> None:
    features: Features = await features_to_dict()
    with open(filename, "w") as file:
        json.dump(features, file, indent=4)


if __name__ == "__main__":
    asyncio.run(export())
