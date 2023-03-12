from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Self, Sequence, TypeVar, overload, runtime_checkable

from discord import Embed, Locale
from discord.utils import MISSING

if TYPE_CHECKING:
    LP = TypeVar("LP", bound="LanguageProtocol")

T = TypeVar("T")

# Protocol for Language and Translations methods are maybe not the best idea
# Will probably change this in the future


@runtime_checkable
class LanguageProtocol(Protocol):
    name: str
    code: str
    locale: Locale | None

    @overload
    @classmethod
    def from_emote(cls, emote: str) -> Self:
        ...

    @overload
    @classmethod
    def from_emote(cls, emote: str, default: T) -> Self | T:
        ...

    @classmethod
    def from_emote(cls, emote: str, default: T = MISSING) -> Self | T:
        ...

    @overload
    @classmethod
    def from_discord_locale(cls, locale: Locale) -> Self:
        ...

    @overload
    @classmethod
    def from_discord_locale(cls, locale: Locale, default: T) -> Self | T:
        ...

    @classmethod
    def from_discord_locale(cls, locale: Locale, default: T = MISSING) -> Self | T:
        ...

    @overload
    @classmethod
    def from_code(cls, code: str) -> Self:
        ...

    @overload
    @classmethod
    def from_code(cls, code: str, default: T) -> Self | T:
        ...

    @classmethod
    def from_code(cls, code: str, default: T = MISSING) -> Self | T:
        ...

    @classmethod
    def available_languages(cls) -> list[Self]:
        ...


class TranslatorFunction(Protocol):
    async def __call__(self, text: str, to: LP, from_: LP | None = None) -> str:
        ...


class BatchTranslatorFunction(Protocol):
    async def __call__(self, texts: Sequence[str], to: LP, from_: LP | None = None) -> Sequence[str]:
        ...


class DetectorFunction(Protocol):
    async def __call__(self, text: str) -> LanguageProtocol | None:
        ...


class SendStrategy(Protocol):
    async def __call__(self, *, content: str = Any, embeds: Sequence[Embed] = Any) -> Any:
        ...


class PreSendStrategy(Protocol):
    async def __call__(self) -> Any:
        ...
