from __future__ import annotations

import gettext
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from json import JSONEncoder
from pathlib import Path
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, cast, overload

import discord
from discord import app_commands

from core.extended_commands import MiscCommand, MiscCommandsType
from core.i18n import translations

if TYPE_CHECKING:
    from mybot import MyBot


FeatureCodebaseTypes = (
    app_commands.Command[Any, ..., Any] | app_commands.Group | app_commands.ContextMenu | MiscCommand[Any, ..., Any]
)


class FeatureType(Enum):
    CHAT_INPUT = "chat_input"
    CONTEXT_USER = "context_user"
    CONTEXT_MESSAGE = "context_message"
    MISC = "misc"


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
    type: FeatureType = FeatureType.CHAT_INPUT
    parameters: list[SlashCommandParameter]
    sub_commands: list[SlashCommand] = field(default_factory=list)
    # parent: SlashCommand | None = None


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
    type: FeatureType = FeatureType.MISC
    misc_type: MiscCommandsType


class Extras(TypedDict):
    beta: NotRequired[bool]
    description: NotRequired[str]  # if ContextMenu
    bot_required_permissions: NotRequired[list[str]]


@overload
def fill_features(
    child: app_commands.Group | app_commands.Command[Any, ..., Any],
    features: list[SlashCommand],
    parent: SlashCommand,
    translations: gettext.GNUTranslations | gettext.NullTranslations = ...,
) -> None: ...


@overload
def fill_features(
    child: FeatureCodebaseTypes,
    features: list[Feature],
    parent: SlashCommand | None = None,
    translations: gettext.GNUTranslations | gettext.NullTranslations = ...,
) -> None: ...


def fill_features(
    child: FeatureCodebaseTypes,
    features: list[Feature] | list[SlashCommand],
    parent: SlashCommand | None = None,
    translations: gettext.GNUTranslations | gettext.NullTranslations = gettext.NullTranslations(),
) -> None:
    extras = cast(Extras, child.extras)

    def shared_kwargs(child: FeatureCodebaseTypes) -> dict[str, Any]:
        return {
            "name": child.name,
            "guild_only": child.guild_only,
            "nsfw": child.nsfw,
            "beta": extras.get("beta", False),
            "soon": extras.get("soon", False),
        }

    match child:
        case app_commands.Command():
            feature = SlashCommand(
                **shared_kwargs(child),
                default_permissions=child.default_permissions.value if child.default_permissions else None,
                description=child.description,
                parameters=[],
                # parent=parent,
            )

            for parameter in child.parameters:
                parameter_payload = SlashCommandParameter(
                    name=parameter.name,
                    description=parameter.description,
                    type=parameter.type.value,
                    required=parameter.required,
                )
                feature.parameters.append(parameter_payload)
        case app_commands.Group():
            feature = SlashCommand(
                **shared_kwargs(child),
                default_permissions=child.default_permissions.value if child.default_permissions else None,
                description=child.description,
                parameters=[],
                sub_commands=[],
                # parent=parent,
            )
            for sub_command in child.commands:
                fill_features(sub_command, feature.sub_commands, feature)
        case app_commands.ContextMenu():
            equiv = {
                discord.AppCommandType.user: FeatureType.CONTEXT_USER,
                discord.AppCommandType.message: FeatureType.CONTEXT_MESSAGE,
            }
            feature = ContextCommand(
                type=equiv[child.type],
                name=child.name,
                guild_only=child.guild_only,
                nsfw=child.nsfw,
                default_permissions=child.default_permissions.value if child.default_permissions else None,
                description=extras.get("description", ""),
                beta=extras.get("beta", False),
                soon=extras.get("soon", False),
            )
        case MiscCommand():
            feature = Misc(
                name=child.name,
                description=child.description,
                guild_only=child.guild_only,
                default_permissions=child.default_permissions,
                beta=child.extras.get("beta", False),
                soon=child.extras.get("soon", False),
                nsfw=child.nsfw,
                misc_type=child.type,
            )

    features.append(feature)  # type: ignore


def extract_features(
    mybot: MyBot,
    translations: gettext.GNUTranslations | gettext.NullTranslations = gettext.NullTranslations(),
) -> list[Feature]:
    features: list[Feature] = []

    for app_command in mybot.tree.get_commands():
        fill_features(app_command, features, translations=translations)

    for misc_cmd in mybot.misc_commands():
        fill_features(misc_cmd, features, translations=translations)

    return features


async def features_exporter(filename: str | Path = Path("./features.json")):
    from mybot import MyBot

    mybot = MyBot(False)
    await mybot.load_extensions()

    # TODO: find out where the unclosed session comes from.
    result: dict[str, list[Feature]] = {}

    for locale, translator in translations.items():
        result[locale.value] = extract_features(mybot, translator)

    def default(o: Any):
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, Enum):
            return o.value

        return JSONEncoder().default(o)

    with open(filename, "w", encoding="utf-8") as file:  # noqa: ASYNC101
        json.dump(result, file, indent=4, default=default)

    for ext in tuple(mybot.extensions):
        await mybot.unload_extension(ext)
