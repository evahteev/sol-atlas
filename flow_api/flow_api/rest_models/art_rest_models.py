from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field
from pytz import utc

from flow_api.rest_models.api_rest_models import ORMBaseModel


class ArtRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    symbol: str | None = None
    description_prompt: str | None = None
    created_at: datetime | None = datetime.now(tz=utc)
    img_picture: str | None = None
    type: str = Field(..., alias="type")
    tags: List | None = None
    parent_id: UUID
    user_id: UUID
    reference_id: UUID
    token_id: int | None = None
    token_address: str | None = None
    nft_token_address: str | None = None
    likes: int = 0
    is_liked: bool = False


class ArtCollectionRest(ORMBaseModel):
    id: UUID
    name: str
    symbol: str | None = None
    address: str | None = None
    parent_id: str | None = None
    base_uri: str | None = None
    created_at: datetime
    type: str = Field(..., alias="type")
    user_id: UUID
    arts: List


class EventRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    type: str = Field(..., alias="type")
    address: str | None = None
    location: str | None = None
    img_event_cover: str | None = None
    user_id: UUID
    reference_id: UUID
    collections: dict


class ArtFinanceRest(ORMBaseModel):
    token_address: str
    burn_total_supply: int
    mint_total_supply: int
    total_supply: int
    guru_balance: int | float
    voting_end_timestamp: int
    participants: int
