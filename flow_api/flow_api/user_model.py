# ruff: noqa: TCH001, TCH003, A003, F821
from __future__ import annotations

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, UUID

import uuid

from flow_api.base_model import Base, int_pk


class UserModel(Base):
    __tablename__ = "user"
    id: str = Column(UUID(as_uuid=True), unique=True,
               primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None]
    email: Mapped[str | None]
    language_code: Mapped[str | None]
    referrer: Mapped[str | None]
    created_at: Mapped[created_at]
    external_id: Mapped[str | None]
    camunda_user_id: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    camunda_key: Mapped[str | None] = Column(UUID(as_uuid=True),
               primary_key=True, default=uuid.uuid4)
    telegram_user_id: Mapped[int_pk | None]
    webapp_user_id: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_suspicious: Mapped[bool] = mapped_column(default=False)
    is_block: Mapped[bool] = mapped_column(default=False)
    is_premium: Mapped[bool] = mapped_column(default=False)

    external_workers = relationship("ExternalWorkerModel", back_populates="user")
    strategy = relationship("StrategyModel", back_populates="user")
    arts = relationship("ArtModel", back_populates="user")
    art_collections = relationship("ArtCollectionModel", back_populates="user")
    events = relationship("EventModel", back_populates="user")
    invites = relationship("InviteModel", back_populates="user")

    def to_dict(self):
        return {
            "id": str(self.id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "email": self.email,
            "language_code": self.language_code,
            "referrer": self.referrer,
            "external_id": self.external_id,
            "camunda_user_id": self.camunda_user_id,
            "camunda_key": str(self.camunda_key),
            "telegram_user_id": self.telegram_user_id,
            "webapp_user_id": self.webapp_user_id,
            "is_admin": self.is_admin,
            "is_suspicious": self.is_suspicious,
            "is_block": self.is_block,
            "is_premium": self.is_premium,
        }
