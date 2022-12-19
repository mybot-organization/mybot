from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils._types import Snowflake


class Emoji(str):
    def __new__(cls, id: Snowflake) -> Emoji:
        return super().__new__(cls, f"<:e:{id}>")

    def __init__(self, id: Snowflake) -> None:
        self._id = id
        super().__init__()

    @property
    def id(self):
        return self._id


class Emojis:
    beta_1 = Emoji(1012449366449078384)
    beta_2 = Emoji(1012449349424390265)
