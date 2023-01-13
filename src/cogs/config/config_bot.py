from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ResponseType, SpecialCog, response_constructor
from core.errors import UnexpectedError
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction

    from mybot import MyBot


logger = logging.getLogger(__name__)


class ConfigBot(SpecialCog["MyBot"], name="config_bot"):
    async def public_translation(self, inter: Interaction, value: bool) -> None:
        if inter.guild_id is None:
            raise UnexpectedError()

        async with self.bot.async_session.begin() as session:
            guild_db = await self.bot.get_guild_db(inter.guild_id, session=session)
            guild_db.translations_are_public = value

        response_text = {
            True: _("Translations will now be public."),
            False: _("Translations will now be private."),
        }
        response = response_constructor(ResponseType.success, response_text[value])
        await inter.response.send_message(**response)
