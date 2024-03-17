from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import ExtendedCog, ResponseType, db, response_constructor
from core.errors import UnexpectedError
from core.i18n import _

if TYPE_CHECKING:
    from discord import Interaction


logger = logging.getLogger(__name__)


class ConfigBot(ExtendedCog, name="config_bot"):
    async def public_translation(self, inter: Interaction, value: bool) -> None:
        if inter.guild_id is None:
            raise UnexpectedError

        async with self.bot.async_session.begin() as session:
            guild_db = await self.bot.get_or_create_db(session, db.GuildDB, guild_id=inter.guild_id)
            guild_db.translations_are_public = value

        response_text = {
            True: _("Translations will now be public."),
            False: _("Translations will now be private."),
        }
        response = response_constructor(ResponseType.success, response_text[value])
        await inter.response.send_message(**response)
