from core import Emojis

COLORS_ORDER = ["blue", "red", "yellow", "purple", "brown", "green", "orange"]
CHOICE_LEGEND_EMOJIS = [getattr(Emojis, f"{color}_round") for color in COLORS_ORDER]
GRAPH_EMOJIS = [getattr(Emojis, f"{color}_mid") for color in COLORS_ORDER]
RIGHT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_right") for color in COLORS_ORDER]
LEFT_CORNER_EMOJIS = [getattr(Emojis, f"{color}_left") for color in COLORS_ORDER]
BOOLEAN_LEGEND_EMOJIS = [Emojis.thumb_down, Emojis.thumb_up]

TOGGLE_EMOTES = {True: Emojis.toggle_on, False: Emojis.toggle_off}
