from __future__ import annotations

from typing import Any, Protocol, Self, Sequence, TypeVar

from discord import Embed, Locale

_LP = TypeVar("_LP", bound="LanguageProtocol")

# Protocol for Language and Translations methods are maybe not the best idea
# Will probably change this in the future


class LanguageProtocol(Protocol):
    name: str
    code: str
    locale: Locale | None

    @classmethod
    def from_emote(cls, emote: str) -> LanguageProtocol | None:
        ...

    @classmethod
    def from_discord_locale(cls, locale: Locale) -> LanguageProtocol | None:
        ...

    @classmethod
    def from_code(cls, code: str) -> Self | None:
        ...

    @classmethod
    def available_languages(cls) -> list[Self]:
        ...


class TranslatorFunction(Protocol):
    async def __call__(self, text: str, to: _LP, from_: _LP | None = None) -> str:
        ...


class BatchTranslatorFunction(Protocol):
    async def __call__(self, texts: Sequence[str], to: _LP, from_: _LP | None = None) -> Sequence[str]:
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
