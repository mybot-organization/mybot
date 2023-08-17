from __future__ import annotations

from typing import Callable

from discord.app_commands import check

from ..misc_command import misc_check as misc_check
from ..utils import CommandType
from .base import T, bot_required_permissions_base, is_me_bool


def bot_required_permissions(**perms: bool) -> Callable[[T], T]:
    return bot_required_permissions_base(CommandType.APP, **perms)


is_me = check(lambda inter: is_me_bool(inter.user.id))
