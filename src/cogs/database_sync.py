from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog, db

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class DatabaseSync(ExtendedCog):
    @ExtendedCog.listener()
    async def on_interaction(self, inter: Interaction):
        print("interaction!")
        await db.update_or_create_user(self.bot)(inter.user)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(DatabaseSync(bot))
