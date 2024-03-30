from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from discord import Interaction, app_commands

from core import ExtendedCog, MiscCommandContext, misc_command
from core.checkers import bot_required_permissions, check, is_activated_predicate, is_user_authorized_predicate

if TYPE_CHECKING:
    from discord import Message

    from mybot import MyBot


logger = logging.getLogger(__name__)


class Restore(ExtendedCog):
    def contains_message_link(self, message: Message) -> bool:
        return bool(re.search(r"<?https://(?:.+\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)", message.content))

    @misc_command(
        "restore",
        description="Send a message back in chat if a link is send.",
        extras={"soon": True},
        trigger_condition=contains_message_link,
    )
    @bot_required_permissions(manage_webhooks=True)
    @check(is_activated_predicate)
    @check(is_user_authorized_predicate)
    async def on_message(self, ctx: MiscCommandContext[MyBot], message: Message) -> None:
        raise NotImplementedError("Restore is not implemented.")

    @app_commands.command()
    async def test(self, inter: Interaction):
        pass


async def setup(bot: MyBot):
    await bot.add_cog(Restore(bot))
