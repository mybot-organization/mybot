from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .languages import Language


type RawDetectionsResponse = list["RawDetections"]
type Detections = list["Detection"]


class RawDetections(TypedDict):
    confidence: float
    language: str


class Detection(TypedDict):
    confidence: float
    language: Language


class Translation(TypedDict):
    translatedText: str


class TranslatePayload(TypedDict):
    q: str
    source: str
    target: str
