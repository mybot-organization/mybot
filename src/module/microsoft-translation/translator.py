from typing import Any
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

    async def translate(self, text: str, to: str, from_: str | None = None) -> str:
        """Translate text

        Args:
            text (str): the text to translate.
            to (str): the language to translate into.
            from_ (str | None, optional): the language to translate from. Defaults to None.

        Returns:
            str: the translated string.
        """
        params = {
            "to": to,
        }
        if from_ is not None:
            params["from"] = from_

        json = [
            {"text": text},
        ]
        try:
            result = await self._request("POST", "/translate", params=params, json=json)
        except aiohttp.ClientResponseError as e:
            raise TranslationError(e) from e

        return result
