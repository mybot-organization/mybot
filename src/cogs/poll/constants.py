from core import Emojis

COLORS_ORDER = ["blue", "red", "yellow", "purple", "brown", "green", "orange"]
COLOR_TO_HEX = {
    "blue": 0x54ACEE,
    "red": 0xDD2D44,
    "yellow": 0xFDCB59,
    "purple": 0xA98ED6,
    "brown": 0xC1694F,
    "green": 0x78B159,
    "orange": 0xF4900E,
}
LEGEND_EMOJIS = [getattr(Emojis, f"{color}_round") for color in COLORS_ORDER]
GRAPH_EMOJIS = [getattr(Emojis, f"{color}_mid") for color in COLORS_ORDER]
RIGHT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_right") for color in COLORS_ORDER]
LEFT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_left") for color in COLORS_ORDER]

DB_VALUE_TO_BOOLEAN = {"0": False, "1": True}
BOOLEAN_INDEXES = {False: 1, True: 0}

TOGGLE_EMOTES = {True: Emojis.toggle_on, False: Emojis.toggle_off}
