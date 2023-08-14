from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import SpecialCog, misc_command
from core.checkers.misc import bot_required_permissions, is_activated, is_user_authorized, misc_check

if TYPE_CHECKING:
    from discord import Message

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Restore(SpecialCog["MyBot"]):
    @misc_command("restore", description="Send a message back in chat if a link is send.", extras={"soon": True})
    @bot_required_permissions(manage_webhooks=True)
    @misc_check(is_activated)
    @misc_check(is_user_authorized)
    async def on_message(self, message: Message) -> None:
        raise NotImplementedError("Restore is not implemented.")


async def setup(bot: MyBot):
    await bot.add_cog(Restore(bot))
