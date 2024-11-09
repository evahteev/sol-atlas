from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ORMBaseModel(BaseModel):
    id: int | UUID | None = None

    class Config:
        from_attributes = True
        response_model_by_alias = True


class RoleRest(ORMBaseModel):
    name: str
    description: str | None = None


class AdminRest(ORMBaseModel):
    last_login: str | None = None
    email: str
    avatar: str | None = None
    intro: str | None = None


class Web3UserRest(ORMBaseModel):
    wallet_address: str
    network_type: str
    user_id: UUID
    # private_key: str | None = None


class TelegramUserRest(ORMBaseModel):
    telegram_id: int
    is_premium: bool
    user_id: UUID


class UserRest(ORMBaseModel):
    id: UUID
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_admin: bool
    is_suspicious: bool
    camunda_user_id: str | None = None
    camunda_key: UUID | None = None
    telegram_user_id: int | None = None
    discord_user_id: str | None = None
    webapp_user_id: UUID | None = None
    is_block: bool
    is_premium: bool
    telegram_accounts: list[TelegramUserRest] = []
    web3_wallets: list[Web3UserRest] = []
    # roles: List[str] = []


class ConfigRest(ORMBaseModel):
    label: str
    key: str
    value: dict | None = None
    status: int


class AuthTokenRest(BaseModel):
    access_token: str
    refresh_token: str


class UsersLeaderBoardRest(BaseModel):
    wallet: str = Field(..., serialization_alias="wallet_address")
    username: str | None = None
    total_burns: float | int = 0
    total_mints: float | int = 0
    total_lock: float | int = Field(..., serialization_alias="total_locked")
    tokens_count: int
    token_addresses: list[str] = Field([], validation_alias="tokens_addesses")
    rank: int = 0


class ArtLeaderBoardRest(BaseModel):
    token_address: str
    name: str
    symbol: str
    total_lock: float | int = Field(..., serialization_alias="total_locked")
    participants: int = Field(..., serialization_alias="participants_count")
    art: Any | None = None
