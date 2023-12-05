from typing import Literal, Never
from urllib.parse import urljoin

import aiohttp

from ._types import TranslatePayload, Translation
from .languages import Language


class LibreTranslate:
    """Interact with the LibreTranslate API."""

    DEFAULT_URL_HOST = "https://translate.argosopentech.com/"

    def __init__(self, host_url: str = DEFAULT_URL_HOST) -> None:
        """Create a LibreAPI connection.

        Args:
            host_url (str): the api host url, if self-hosted. Defaults to "https://translate.argosopentech.com/".
        """

        self.host_url = host_url
        self.client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))

    async def close(self):
        """Close the connection."""
        await self.client.close()

    async def translate(self, text: str, to: Language, from_: Language | Literal["auto"] = "auto") -> str:
        """Translate text

        Args:
            text (str): the text to translate.
            to (Languages): the language to translate into.
            from_ (Languages | None, optional): the language to translate from. Defaults to None.

        Returns:
            str: the translated string.
        """
        payload = TranslatePayload(q=text, source="auto" if from_ == "auto" else from_.value, target=to.value)
        headers = {"Content-Type": "application/json"}

        async with self.client.post(
            urljoin(self.host_url, "/translate"),
            json=payload,
            headers=headers,
        ) as response:
            raw: Translation = await response.json()
        return raw["translatedText"]

    async def detect(self) -> Never:
        raise NotImplementedError()
