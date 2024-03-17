from abc import ABC, abstractmethod
from collections.abc import Sequence

from .languages import Language, Languages


class TranslatorAdapter(ABC):
    async def close(self):
        """
        The method is called if the Cog is closed.
        """

    @abstractmethod
    async def translate(self, text: str, to: Language, from_: Language | None = None) -> str: ...

    @abstractmethod
    async def batch_translate(self, texts: Sequence[str], to: Language, from_: Language | None = None) -> list[str]: ...

    @abstractmethod
    async def detect(self, text: str) -> Language | None: ...

    @abstractmethod
    async def available_languages(self) -> Languages: ...
