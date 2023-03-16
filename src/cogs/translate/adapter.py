from abc import ABC, abstractmethod
from typing import Self, Sequence, TypeVar

from discord import Locale
from discord.utils import MISSING

T = TypeVar("T")
L = TypeVar("L", bound="LanguageAdapter", covariant=True)


class LanguageAdapter(ABC):
    @classmethod
    @abstractmethod
    async def from_emote(cls, emote: str, default: T = MISSING) -> Self | T:
        ...

    @classmethod
    @abstractmethod
    def from_discord_locale(cls, locale: Locale, default: T = MISSING) -> Self | T:
        ...

    @classmethod
    @abstractmethod
    def from_code(cls, code: str, default: T = MISSING) -> Self | T:
        ...

    @classmethod
    @abstractmethod
    def available_languages(cls) -> list[Self]:
        ...


class TranslatorAdapter(ABC):
    @abstractmethod
    async def translate(self, text: str, to: Self, from_: Self | None = None) -> str:
        ...

    @abstractmethod
    async def batch_translate(self, texts: Sequence[str], to: Self, from_: Self | None = None) -> list[str]:
        ...

    @abstractmethod
    async def detect(self, text: str) -> Self | None:
        ...
