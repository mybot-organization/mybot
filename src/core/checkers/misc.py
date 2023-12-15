from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ..extended_commands import MiscCommandContext, misc_check as misc_check
from ..utils import CommandType
from .base import T, bot_required_permissions_base

if TYPE_CHECKING:
    from mybot import MyBot


def bot_required_permissions(**perms: bool) -> Callable[[T], T]:
    return bot_required_permissions_base(CommandType.MISC, **perms)


async def is_user_authorized(context: MiscCommandContext[MyBot]) -> bool:
    del context  # unused
    # TODO(airo.pi_): check using the database if the user is authorized
    return True


async def is_activated(context: MiscCommandContext[MyBot]) -> bool:
    del context  # unused
    # TODO(airo.pi_): check using the database if the misc command is activated
    return True
