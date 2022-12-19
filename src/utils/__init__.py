import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Iterator, Literal, Mapping, TypedDict, overload

import discord
from discord import Embed

from ._config import config as config

logger = logging.getLogger(__name__)


class Response(TypedDict):
    embed: Embed | None
    content: str | None


@dataclass()
class _Response(Mapping[str, Embed]):
    embed: Embed | None = None
    content: str | None = None

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    def __len__(self) -> int:
        return self.__dict__.__len__()


class _ResponseEmbed(_Response):
    embed: Embed
    content: str | None = None


class ResponseType(Enum):
    success = auto()
    info = auto()
    error = auto()
    warning = auto()


_embed_colors = {
    ResponseType.success: discord.Color.brand_green(),
    ResponseType.info: discord.Color.blurple(),
    ResponseType.error: discord.Color.brand_red(),
    ResponseType.warning: discord.Color.yellow(),
}

_embed_author_icon_urls = {
    ResponseType.success: "https://cdn.discordapp.com/attachments/584397334608084992/1007741457328787486/success.png",
    ResponseType.info: "https://cdn.discordapp.com/attachments/584397334608084992/1007741456708022293/info.png",
    ResponseType.error: "https://cdn.discordapp.com/attachments/584397334608084992/1007741455483281479/error.png",
    ResponseType.warning: "https://cdn.discordapp.com/attachments/584397334608084992/1007741457819516999/warning.png",
}


@overload
def response_constructor(response_type: ResponseType, message: str, embedded: Literal[True] = ...) -> _ResponseEmbed:
    ...


@overload
def response_constructor(response_type: ResponseType, message: str, embedded: Literal[False] = ...) -> _Response:
    ...


def response_constructor(response_type: ResponseType, message: str, embedded: bool = True) -> _Response:
    embed = discord.Embed(
        color=_embed_colors[response_type],
    )

    if len(message) > 256:
        logger.warning(f'This error message is too long to be displayed in author field. "{message}"')

    embed.set_author(name=message, icon_url=_embed_author_icon_urls[response_type])

    return _Response(embed=embed)
