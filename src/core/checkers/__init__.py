from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import discord
from discord import Interaction
from discord.app_commands import Command, ContextMenu, check as app_check

from .._config import config
from .._types import CoroT
from ..errors import BotMissingPermissions, NotAllowedUser
from ..extended_commands import MiscCommandContext, check as misc_check
from ..utils import CommandType
from .max_concurrency import MaxConcurrency as MaxConcurrency

if TYPE_CHECKING:
    from mybot import MyBot

    type Context = Interaction | MiscCommandContext[Any]


logger = logging.getLogger(__name__)


def _determine_type(obj: Any) -> CommandType:
    """This function will determine the type of the command.

    It makes some assumptions about the type of the command based on the annotations of the function.
    """
    if isinstance(obj, Command | ContextMenu):
        return CommandType.APP
    if hasattr(obj, "__listener_as_command__"):
        return CommandType.MISC
    else:
        annotations = inspect.get_annotations(obj)
        target = next(iter(annotations.values()))  # get the first annotation
        if target is MiscCommandContext:
            return CommandType.MISC
        if target is Interaction:
            return CommandType.APP
        if isinstance(target, str):
            # I don't know how to handle this case properly because MyBot is not imported in this file
            if target.startswith("Interaction"):
                return CommandType.APP
            if target.startswith("MiscCommandContext"):
                return CommandType.MISC
    raise TypeError("Could not determine the type of the command.")


def _add_extra[T](type_: CommandType, func: T, name: str, value: Any) -> T:
    copy_func = func  # typing behavior
    if type_ is CommandType.APP:
        if isinstance(func, Command | ContextMenu):
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


def check[C: Interaction | MiscCommandContext[Any], F](
    predicate: Callable[[C], bool | CoroT[bool]],
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        match _determine_type(func):
            case CommandType.APP:
                p = cast(Callable[[Interaction], bool | CoroT[bool]], predicate)
                return app_check(p)(func)
            case CommandType.MISC:
                p = cast(Callable[[MiscCommandContext[Any]], bool | CoroT[bool]], predicate)
                return misc_check(p)(func)

    return decorator


def _bot_required_permissions_test(perms: dict[str, bool]) -> Callable[..., bool]:
    def predicate(ctx: Context):
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


def bot_required_permissions[T](**perms: bool) -> Callable[[T], T]:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {", ".join(invalid)}")

    def decorator(func: T) -> T:
        type_ = _determine_type(func)
        _add_extra(
            type_,
            func,
            "bot_required_permissions",
            [perm for perm, value in perms.items() if value is True],
        )
        match type_:
            case CommandType.APP:
                return app_check(_bot_required_permissions_test(perms))(func)
            case CommandType.MISC:
                return misc_check(_bot_required_permissions_test(perms))(func)

    return decorator


async def is_user_authorized_predicate(context: MiscCommandContext[MyBot]) -> bool:
    del context  # unused
    # TODO(airo.pi_): check using the database if the user is authorized
    return True


is_user_authorized = check(is_user_authorized_predicate)  # misc commands only


async def is_activated_predicate(context: MiscCommandContext[MyBot]) -> bool:
    del context  # unused
    # TODO(airo.pi_): check using the database if the misc command is activated
    return True


is_activated = check(is_activated_predicate)  # misc commands only


def allowed_users_test(*user_ids: int) -> Callable[..., bool]:
    def inner(user_id: int) -> bool:
        if user_id not in user_ids:
            raise NotAllowedUser(user_id)
        return True

    return inner


is_me_test = allowed_users_test(*config.owners_ids)  # test function used for eval commands
is_me = check(lambda ctx: is_me_test(ctx.user.id))
