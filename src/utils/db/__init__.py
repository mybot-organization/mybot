from __future__ import annotations

import logging
import sys
from os import environ
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import create_async_engine

from .tables import guilds as guilds

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

try:
    POSTGRES_USER = environ["POSTGRES_USER"]
    POSTGRES_PASSWORD = environ["POSTGRES_PASSWORD"]
    POSTGRES_DB = environ["POSTGRES_DB"]
except KeyError as e:
    logger.critical(f"Missing environment variable {e}.")
    sys.exit(1)

db: AsyncEngine = create_async_engine(
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@database:5432/{POSTGRES_DB}"
)
