from sqlalchemy.orm import DeclarativeBase

from warehouse_api.db.meta import meta


class Base(DeclarativeBase):
    """Base for all models."""

    metadata = meta
