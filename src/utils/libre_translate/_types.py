from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypedDict

if TYPE_CHECKING:
    from .languages import Language


RawDetectionsResponse: TypeAlias = list["RawDetections"]


class RawDetections(TypedDict):
    confidence: float
    language: str


Detections: TypeAlias = list["Detection"]


class Detection(TypedDict):
    condidence: float
    language: Language


class Translation(TypedDict):
    translatedText: str


class TranslatePayload(TypedDict):
    q: str
    source: str
    target: str
