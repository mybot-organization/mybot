from __future__ import annotations

from typing import Any
from collections.abc import Iterable
from urllib.parse import urljoin

import aiohttp


class TranslationError(Exception):
    pass


class MicrosoftTranslator:
    _base_url = "https://api.cognitive.microsofttranslator.com/"
    _api_version = "3.0"

    def __init__(self, token: str, region: str = "eastus"):
        self._token = token
        self._region = region
        self._client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))

    async def close(self):
        """Close the connection."""
        await self._client.close()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = urljoin(self._base_url, endpoint)
        headers = {
            "Ocp-Apim-Subscription-Key": self._token,
            "Ocp-Apim-Subscription-Region": self._region,
            "Content-Type": "application/json; charset=UTF-8",
        }

        kwargs.setdefault("params", {})
        kwargs["params"] |= {"api-version": self._api_version}

        async with self._client.request(method, url, headers=headers, **kwargs) as response:
            return await response.json()

    async def translate(self, texts: Iterable[str], to: str, from_: str | None = None) -> list[TranslationResult]:
        """Translate text

        Args:
            text: the text to translate.
            to: the language to translate into.
            from_: the language to translate from. Defaults to None.

        Returns:
            the translated string.
        """
        if isinstance(texts, str):
            texts = [texts]

        params = {
            "to": to,
        }
        if from_ is not None:
            params["from"] = from_

        json = [{"text": text} for text in texts]
        try:
            result = await self._request("POST", "/translate", params=params, json=json)
        except aiohttp.ClientResponseError as e:
            raise TranslationError(e) from e

        return [TranslationResult(**r) for r in result]


class DetectionResult:
    def __init__(self, language: str, score: float):
        self.language: str = language
        self.score: float = score

    def __repr__(self) -> str:
        return f'<DetectionResult language="{self.language}" score={self.score}>'


class TranslationPerLanguageResult:
    def __init__(self, text: str, to: str):
        self.text: str = text
        self.to: str = to

    def __repr__(self) -> str:
        return f'<TranslationPerLanguageResult text="{self.text}" to={self.to}>'


class TranslationResult:
    def __init__(self, **kwargs: Any):
        self.detected_language: DetectionResult | None = (
            DetectionResult(**raw) if (raw := kwargs.get("detectedLanguage")) else None
        )
        self.value = [TranslationPerLanguageResult(**t) for t in kwargs["translations"]]

    def __repr__(self) -> str:
        return f"<TranslationResult detected_language={self.detected_language} translations={self.value}>"
