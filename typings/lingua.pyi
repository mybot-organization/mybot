from enum import Enum, auto
from typing import Self

class Language(Enum):
    ENGLISH = auto()
    ARABIC = auto()
    CHINESE = auto()
    FRENCH = auto()
    GERMAN = auto()
    HINDI = auto()
    INDONESIAN = auto()
    IRISH = auto()
    ITALIAN = auto()
    JAPANESE = auto()
    KOREAN = auto()
    POLISH = auto()
    PORTUGUESE = auto()
    RUSSIAN = auto()
    SPANISH = auto()
    TURKISH = auto()
    VIETNAMESE = auto()

class LanguageDetectorBuilder:
    @classmethod
    def from_languages(cls, *args: Language) -> Self: ...
    def with_low_accuracy_mode(self) -> Self: ...
    def with_minimum_relative_distance(self, value: float) -> Self: ...
    def build(self) -> LanguageDetector: ...

class LanguageDetector:
    def detect_language_of(self, text: str) -> Language | None: ...
