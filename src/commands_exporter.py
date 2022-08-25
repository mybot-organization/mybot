from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypedDict, cast

from discord import app_commands
from typing_extensions import NotRequired

if TYPE_CHECKING:
    from mybot import MyBot


@dataclass
class Features:
    slash_commands: list[SlashCommand]
    context_commands: list[ContextCommand]


@dataclass
class Command:
    name: str
    guild_only: bool
    nsfw: bool
    default_permissions: int | None
    beta: bool


@dataclass
class SlashCommand(Command):
    description: str
    parameters: list[SlashCommandParameter]


@dataclass
class SlashCommandParameter:
    name: str
    description: str
    required: bool
    type: int


class Extras(TypedDict):
    beta: NotRequired[bool]


class ContextCommand(Command):
    type: Literal["user", "message"]


def features_to_dict(mybot: MyBot) -> Features:
    features = Features(slash_commands=[], context_commands=[])

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

            features.slash_commands.append(slash_command)

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
