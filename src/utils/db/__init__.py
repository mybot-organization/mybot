from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import create_async_engine

from .. import config
from .tables import guilds as guilds

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

if config.POSTGRES_PASSWORD is None:
    logger.critical(f"Missing environment variable POSTGRES_PASSWORD.")
    sys.exit(1)

db: AsyncEngine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@database:5432/{config.POSTGRES_DB}"
)
