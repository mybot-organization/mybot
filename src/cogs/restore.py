from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import SpecialCog, misc_command
from core.i18n import _

if TYPE_CHECKING:
    from discord import Message

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Restore(SpecialCog["MyBot"]):
    @misc_command("restore", description="Send a message back in chat if a link is send.")
    async def on_message(self, message: Message) -> None:
        raise NotImplementedError("Calculator is not implemented.")


async def setup(bot: MyBot):
    await bot.add_cog(Restore(bot))
