from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypeVar
from collections.abc import Callable

import discord
from discord.app_commands import Command, ContextMenu, check as app_check

from .._config import config
from ..errors import BotMissingPermissions, NotAllowedUser
from ..extended_commands import MiscCommandContext, misc_check as misc_check
from ..utils import CommandType

T = TypeVar("T")


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


def add_extra(type_: CommandType, func: T, name: str, value: Any) -> T:
    copy_func = func  # typing behavior
    if type_ is CommandType.APP:
        if isinstance(func, (Command, ContextMenu)):
            func.extras[name] = value
        else:
            logger.critical(
                "Because we need to add extras, this decorator must be above the command decorator. "
                "(Command should already be defined)"
            )
    elif type_ is CommandType.MISC:
        if hasattr(func, "__listener_as_command__"):
            command: Command[Any, ..., Any] = getattr(func, "__listener_as_command__")
            command.extras[name] = value
        else:
            if not hasattr(func, "__misc_commands_extras__"):
                setattr(func, "__misc_commands_extras__", {})
            getattr(func, "__misc_commands_extras__")[name] = value
    return copy_func


def _bot_required_permissions_predicate(perms: dict[str, bool]) -> Callable[..., bool]:
    def predicate(ctx: Interaction | MiscCommandContext[MyBot]):
        match ctx:
            case discord.Interaction():
                permissions = ctx.app_permissions
            case MiscCommandContext():
                permissions = ctx.bot_permissions

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(missing)

    return predicate


# This exist only to avoid the duplication of invalid perms check. It mays be removed in the future.
def bot_required_permissions_base(type_: CommandType, **perms: bool) -> Callable[[T], T]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {", ".join(invalid)}")

    def decorator(func: T) -> T:
        match type_:
            case CommandType.APP:
                add_extra(
                    type_, func, "bot_required_permissions", [perm for perm, value in perms.items() if value is True]
                )
                return app_check(_bot_required_permissions_predicate(perms))(func)
            case CommandType.MISC:
                add_extra(
                    CommandType.MISC,
                    func,
                    "bot_required_permissions",
                    [perm for perm, value in perms.items() if value is True],
                )
                return misc_check(_bot_required_permissions_predicate(perms))(func)

    return decorator


def allowed_users_bool(*user_ids: int) -> Callable[..., bool]:
    def inner(user_id: int) -> bool:
        if user_id not in user_ids:
            raise NotAllowedUser(user_id)
        return True

    return inner


is_me_bool = allowed_users_bool(*config.OWNERS_IDS)
