from __future__ import annotations

from typing import Any, NamedTuple, Protocol, TypeVar

from discord import Locale

T = TypeVar("T")
L = TypeVar("L", covariant=True)


class LanguageImplementation(Protocol):
    name: str
    code: str

    @classmethod
    def from_emote(cls, emote: str) -> LanguageImplementation | None:
        ...

    @classmethod
    def from_discord_locale(cls, locale: Locale) -> LanguageImplementation | None:
        ...

    @classmethod
    def from_code(cls, code: str) -> LanguageImplementation | None:
        ...

    @staticmethod
    def available_languages() -> list[LanguageImplementation]:
        ...


class TranslatorFunction(Protocol):
    async def __call__(self, text: str, to: LanguageImplementation, from_: LanguageImplementation | None = None) -> str:
        ...


class SendStrategy(Protocol):
    async def __call__(self, *, content: str) -> Any:
        ...


class PreSendStrategy(Protocol):
    async def __call__(self) -> Any:
        ...


class StrategyNatures(NamedTuple):
    pre: PreSendStrategy
    send: SendStrategy


class Strategies(NamedTuple):
    private: StrategyNatures
    public: StrategyNatures
