from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._types import Snowflake


class Emoji(str):
    def __new__(cls, id: Snowflake) -> Emoji:
        return super().__new__(cls, f"<:_:{id}>")

    def __init__(self, id: Snowflake) -> None:
        self._id = id
        super().__init__()

    @property
    def id(self):
        return self._id


class Emojis:
    beta_1 = Emoji(1012449366449078384)
    beta_2 = Emoji(1012449349424390265)

    two048_2 = Emoji(1068989299808292956)
    two048_4 = Emoji(1068989301888663604)
    two048_8 = Emoji(1068989303243415672)
    two048_16 = Emoji(1068989304912756807)
    two048_32 = Emoji(1068989307349635133)
    two048_64 = Emoji(1068989309119643770)
    two048_128 = Emoji(1068989310268887061)
    two048_256 = Emoji(1068989312529596546)
    two048_512 = Emoji(1068989314127626321)
    two048_1024 = Emoji(1068989316195426395)
    two048_2048 = Emoji(1068989317592121446)
    two048_4096 = Emoji(1068989378413744231)
    two048_8192 = Emoji(1068989381379096646)
    two048_empty = Emoji(1068990458929365072)

    up_arrow = Emoji(1069018469036736544)
    down_arrow = Emoji(1069018464301363240)
    left_arrow = Emoji(1069018466624995439)
    right_arrow = Emoji(1069018468185288834)
