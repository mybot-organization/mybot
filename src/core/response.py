import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import discord
from discord import Color, Embed

logger = logging.getLogger(__name__)


@dataclass
class MessageDisplay(Mapping[str, Embed | str | None]):
    """
    Used to represent the "display" of a message. It contains the content, the embeds, etc...
    """

    embed: Embed
    content: str | None = None

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dataclass_fields__)

    def __len__(self) -> int:
        return self.__dataclass_fields__.__len__()


class UneditedMessageDisplay(Mapping[str, Any]):
    """
    Used as an empty dict. By doing Message.edit(**UneditedMessageDisplay()), the message will remain unchanged.
    """

    def __getitem__(self, key: str) -> Any:
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter([])

    def __len__(self) -> int:
        return 0


class ResponseType(Enum):
    success = auto()
    info = auto()
    error = auto()
    warning = auto()


_embed_colors = {
    ResponseType.success: Color.brand_green(),
    ResponseType.info: Color.blurple(),
    ResponseType.error: Color.brand_red(),
    ResponseType.warning: Color.yellow(),
}

_embed_author_icon_urls = {
    ResponseType.success: "https://cdn.discordapp.com/attachments/584397334608084992/1007741457328787486/success.png",
    ResponseType.info: "https://cdn.discordapp.com/attachments/584397334608084992/1007741456708022293/info.png",
    ResponseType.error: "https://cdn.discordapp.com/attachments/584397334608084992/1007741455483281479/error.png",
    ResponseType.warning: "https://cdn.discordapp.com/attachments/584397334608084992/1007741457819516999/warning.png",
}


def response_constructor(
    response_type: ResponseType, message: str, embedded: bool = True, author_url: str | None = None
) -> MessageDisplay:
    del embedded  # TODO(airo.pi_)
    embed = discord.Embed(
        color=_embed_colors[response_type],
    )

    if len(message) > 256:
        logger.warning('This error message is too long to be displayed in author field. "%s"', message)
        message = message[:253] + "..."

    embed.set_author(name=message, icon_url=_embed_author_icon_urls[response_type], url=author_url)

    return MessageDisplay(embed=embed)
