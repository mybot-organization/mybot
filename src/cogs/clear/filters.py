from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import discord
from discord.utils import get

from core import SizedMapping

from .enums import Has, Pinned

if TYPE_CHECKING:
    from discord.types.embed import EmbedType


class Filter(ABC):
    """A filter is a test that returns True if a message should be deleted, False otherwise."""

    @abstractmethod
    async def test(self, message: discord.Message) -> bool:
        """Return True if the message should be deleted, False otherwise."""
        ...


class RegexFilter(Filter):
    def __init__(self, pattern: re.Pattern[str]):
        self.pattern = pattern

    @classmethod
    def from_string(cls, string: str) -> RegexFilter:
        return cls(re.compile(string, re.MULTILINE))

    async def test(self, message: discord.Message) -> bool:
        return bool(self.pattern.search(message.content))


class UserFilter(Filter):
    def __init__(self, user_id: int):
        self.user_id = user_id

    @classmethod
    def from_user(cls, user: discord.User) -> UserFilter:
        return cls(user.id)

    async def test(self, message: discord.Message) -> bool:
        return message.author.id == self.user_id


class RoleFilter(Filter):
    members_cache = SizedMapping[str, discord.Member](max_size=100)

    def __init__(self, role_id: int):
        self.role_id = role_id

    @classmethod
    def from_role(cls, role: discord.Role) -> RoleFilter:
        return cls(role.id)

    async def test(self, message: discord.Message) -> bool:
        guild = cast(discord.Guild, message.guild)  # at this point, we know the guild is not None
        member = guild.get_member(message.author.id) or self.members_cache.get(f"{guild.id}.{message.author.id}")
        if member is None:
            try:
                member = await guild.fetch_member(message.author.id)
            except discord.HTTPException:
                return False
            self.members_cache[f"{guild.id}.{message.author.id}"] = member

        return get(member.roles, id=self.role_id) is not None


class PinnedFilter(Filter):
    def __init__(self, pinned: Pinned):
        self.pinned = pinned

    @classmethod
    def default(cls) -> PinnedFilter:
        return cls(Pinned.exclude)

    async def test(self, message: discord.Message) -> bool:
        match self.pinned:
            case Pinned.include:
                return True
            case Pinned.exclude:
                return not message.pinned
            case Pinned.only:
                return message.pinned


class HasFilter(Filter):
    image_content_type_re = re.compile(r"^image\/.*")
    video_content_type_re = re.compile(r"^video\/.*")
    audio_content_type_re = re.compile(r"^audio\/.*")
    has_link_re = re.compile(
        r"(?i)\b(?:(?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\((?:[^\s()<>]+|"
        r"(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"  # noqa: RUF001
    )
    has_discord_invite_re = re.compile(r"discord(?:app)?\.(?:gg|com/invite)\/([a-zA-Z0-9]+)")

    def __init__(self, has: Has):
        self.has = has

    async def check_types(
        self, message: discord.Message, content_type_re: re.Pattern[str], embed_types: tuple[EmbedType, ...]
    ) -> bool:
        for attachment in message.attachments:
            if attachment.content_type is None:
                continue
            if content_type_re.match(attachment.content_type):
                return True
        return any(any(embed.type == t for t in embed_types) for embed in message.embeds)

    async def test(self, message: discord.Message) -> bool:
        match self.has:
            case Has.image:
                return await self.check_types(message, self.image_content_type_re, ("image", "gifv"))
            case Has.video:
                return await self.check_types(message, self.video_content_type_re, ("video",))
            case Has.audio:
                return await self.check_types(message, self.audio_content_type_re, ())
            case Has.stickers:
                return bool(message.stickers)
            case Has.files:
                return bool(message.attachments)
            case Has.embed:
                return bool(message.embeds)
            case Has.link:
                return bool(self.has_link_re.search(message.content))
            case Has.mention:
                return bool(message.mentions or message.role_mentions)
            case Has.discord_invite:
                return bool(self.has_discord_invite_re.search(message.content))


class LengthFilter(Filter):
    def __init__(self, length_test: Callable[[int, int], bool], length: int):
        self.length_test = length_test
        self.length = length

    async def test(self, message: discord.Message) -> bool:
        return self.length_test(len(message.content), self.length)
