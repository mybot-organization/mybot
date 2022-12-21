from __future__ import annotations

from typing import Any, NamedTuple, Protocol, TypeVar

from discord import Locale

LI = TypeVar("LI", bound="LanguageImplementation")


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
    async def __call__(self, text: str, to: LI, from_: LI | None = None) -> str:
        ...


class SendStrategy(Protocol):
    async def __call__(self, *, content: str) -> Any:
        ...


class PreSendStrategy(Protocol):
    async def __call__(self) -> Any:
        ...


class Strategies(NamedTuple):
    pre: PreSendStrategy
    send: SendStrategy


class StrategiesSet(NamedTuple):
    private: Strategies
    public: Strategies
