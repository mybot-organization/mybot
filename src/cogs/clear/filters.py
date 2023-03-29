from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import cast

import discord
from aiohttp import ClientError, ClientSession, ClientTimeout
from discord.utils import get

from core import SizedMapping

from .enums import Has, Pinned


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
    image_content_type = re.compile(r"^image\/.*")
    has_link = re.compile(
        (
            r"(?i)\b(?:(?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\((?:[^\s()<>]+|"
            r"(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        )
    )

    def __init__(self, has: Has):
        self.has = has

    async def get_link(self, link: str) -> str | None:
        session_timeout = ClientTimeout(total=None, sock_connect=1, sock_read=1)
        async with ClientSession(timeout=session_timeout) as session:
            async with session.head(link) as response:
                return response.headers.get("Content-Type", None)

    async def test(self, message: discord.Message) -> bool:
        attachments = message.attachments
        match self.has:
            case Has.image:
                if not (result := self.has_link.findall(message.content)) and not attachments:
                    return False
                for attachment in attachments:
                    if attachment.content_type is None:
                        continue
                    if self.image_content_type.match(attachment.content_type):
                        return True
                for match in result:
                    try:
                        content_type = await self.get_link(match)
                    except ClientError:
                        continue

                    if content_type is None:
                        continue
                    if self.image_content_type.match(content_type):
                        return True
                return False
