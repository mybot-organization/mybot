from enum import Enum


class Pinned(Enum):
    include = 1
    exclude = 2
    only = 3


class Has(Enum):
    image = 1
    video = 2
    audio = 3
    stickers = 4
    files = 5
    any_attachment = 6
    embed = 7
    link = 8
    mention = 9
    discord_invite = 10
