from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ._types import Snowflake


class Emoji(str):
    def __new__(cls, id: Snowflake) -> Self:
        return super().__new__(cls, f"<:e:{id}>")

    def __init__(self, id: Snowflake) -> None:
        self._id = id
        super().__init__()

    @property
    def id(self):
        return self._id


class Emojis:
    beta_1 = Emoji(1083897907981320272)
    beta_2 = Emoji(1083897910728609872)

    soon_1 = Emoji(1083897922522988575)
    soon_2 = Emoji(1083897924146180198)

    toggle_off = Emoji(1077634526844567603)
    toggle_on = Emoji(1077634491729838180)

    blue_round = Emoji(1077941067002945637)
    blue_mid = Emoji(1077941062552797234)
    blue_left = Emoji(1077941064733827233)
    blue_right = Emoji(1077941065929216030)

    red_round = Emoji(1077960826843037817)
    red_mid = Emoji(1077960822418063401)
    red_left = Emoji(1077960823617622166)
    red_right = Emoji(1077960825521832067)

    yellow_round = Emoji(1077960141426655312)
    yellow_mid = Emoji(1077960139967037460)
    yellow_left = Emoji(1077941105632481302)
    yellow_right = Emoji(1077941888109252609)

    purple_round = Emoji(1077941876008698038)
    purple_mid = Emoji(1077941874704252999)
    purple_left = Emoji(1077941087890583573)
    purple_right = Emoji(1077941091325714472)

    brown_round = Emoji(1077941073252450344)
    brown_mid = Emoji(1077941068118642768)
    brown_left = Emoji(1077941070043828336)
    brown_right = Emoji(1077941071297925150)

    green_round = Emoji(1077941074523340820)
    green_mid = Emoji(1077941869511721001)
    green_left = Emoji(1077941080680575057)
    green_right = Emoji(1077941872519024660)

    white_round = Emoji(1077941885013860402)
    white_mid = Emoji(1077941098493784124)
    white_left = Emoji(1077941883763949599)
    white_right = Emoji(1077941101790511124)

    orange_round = Emoji(1077941083624984628)
    orange_mid = Emoji(1077941867133546566)
    orange_left = Emoji(1077941871009091594)
    orange_right = Emoji(1077960256317042759)

    thumb_up = "👍"
    thumb_down = "👎"
