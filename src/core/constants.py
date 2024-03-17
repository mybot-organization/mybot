from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Self

from discord.app_commands import TranslationContextLocation

if TYPE_CHECKING:
    from ._types import Snowflake


def _identity[T](x: T) -> T:
    return x


_ = _identity


class Emoji(str):
    __slots__ = ("id",)

    def __new__(cls, id: Snowflake) -> Self:
        return super().__new__(cls, f"<:_:{id}>")

    def __init__(self, id: Snowflake) -> None:
        self._id = id
        super().__init__()

    @property
    def id(self):
        return self._id


class Emojis:
    beta_1 = Emoji(1083897907981320272)
    beta_2 = Emoji(1083897910728609872)

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

    soon_1 = Emoji(1083897922522988575)
    soon_2 = Emoji(1083897924146180198)

    misc_command_reaction = Emoji(1084116094245163141)
    misc_command_text = Emoji(1084118001088999544)

    slash_command = Emoji(1084137615609057351)
    message_context = Emoji(1084139743484334151)

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


class EmbedsCharLimits(enum.Enum):
    TITLE = 256
    DESCRIPTION = 4096
    FIELDS_NAME = 256
    FIELDS_VALUE = 1024
    FOOTER_TEXT = 2048
    AUTHOR_NAME = 256


class GeneralCharLimits(enum.Enum):
    MESSAGE_TOTAL = 6000
    MESSAGE_CONTENT = 2000
    SLASH_COMMAND_TOTAL = 4000


class TranslationContextLimits(enum.Enum):
    CHOICE_NAME = 100
    COMMAND_DESCRIPTION = 100
    PARAMETER_DESCRIPTION = 100
    PARAMETER_NAME = 100
    COMMAND_NAME = 100
    GROUP_NAME = 100
    GROUP_DESCRIPTION = 100

    @classmethod
    def from_location(cls, location: TranslationContextLocation) -> TranslationContextLimits | None:
        translation_context_limits_bind = {
            TranslationContextLocation.choice_name: TranslationContextLimits.CHOICE_NAME,
            TranslationContextLocation.command_description: TranslationContextLimits.COMMAND_DESCRIPTION,
            TranslationContextLocation.parameter_description: TranslationContextLimits.PARAMETER_DESCRIPTION,
            TranslationContextLocation.parameter_name: TranslationContextLimits.PARAMETER_NAME,
            TranslationContextLocation.command_name: TranslationContextLimits.COMMAND_NAME,
            TranslationContextLocation.group_name: TranslationContextLimits.GROUP_NAME,
            TranslationContextLocation.group_description: TranslationContextLimits.GROUP_DESCRIPTION,
        }
        return translation_context_limits_bind.get(location)


# keys are from discord.Permissions, so some can defer from the discord API
# values are the version showed in the Discord UI.
human_permissions = {
    "create_instant_invite": _("Create Invite"),
    "kick_members": _("Kick Members"),
    "ban_members": _("Ban Members"),
    "administrator": _("Administrator"),
    "manage_channels": _("Manage Channels"),
    "manage_guild": _("Manage Server"),
    "add_reactions": _("Add Reactions"),
    "view_audit_log": _("View Audit Log"),
    "priority_speaker": _("Priority Speaker"),
    "stream": _("Video"),
    "read_messages": _("View Channel"),
    "send_messages": _("Send Messages"),
    "send_tts_messages": _("Send Text-to-speech Messages"),
    "manage_messages": _("Manage Messages"),
    "embed_links": _("Embed Links"),
    "attach_files": _("Attach Files"),
    "read_message_history": _("Read Message History"),
    "mention_everyone": _("Mention @everyone, @here and All Roles"),
    "external_emojis": _("Use External Emojis"),
    "view_guild_insights": _("View Guild Insights"),
    "connect": _("Connect"),
    "speak": _("Speak"),
    "mute_members": _("Mute Members"),
    "deafen_members": _("Deafen Members"),
    "move_members": _("Move Members"),
    "use_voice_activation": _("Use Voice Activity"),
    "change_nickname": _("Change Nickname"),
    "manage_nicknames": _("Manage Nicknames"),
    "manage_roles": _("Manage Roles"),
    "manage_webhooks": _("Manage Webhooks"),
    "manage_expressions": _("Manage Expressions"),
    "use_application_commands": _("Use Application Commands"),
    "request_to_speak": _("Request to Speak"),
    "manage_events": _("Manage Events"),
    "manage_threads": _("Manage Threads"),
    "create_public_threads": _("Create Public Threads"),
    "create_private_threads": _("Create Private Threads"),
    "external_stickers": _("Use External Stickers"),
    "send_messages_in_threads": _("Send Messages in Threads"),
    "use_embedded_activities": _("Use Activities"),
    "moderate_members": _("Time out members"),
    "use_soundboard": _("Use Soundboard"),
    "create_expressions": _("Create Expressions"),
    "use_external_sounds": _("Use External Sounds"),
    "send_voice_messages": _("Send Voice Messages"),
}
