import asyncio
import json
import logging
import pathlib
import random
import re
import uuid
from datetime import datetime, timedelta
from functools import partial
from typing import Annotated, List, Optional

import aiohttp
import httpx
from aiocache import caches
from aiocache.decorators import cached
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.params import Path, Query
from pydantic import UUID4
from redis.exceptions import ConnectionError
from starlette.requests import Request
from starlette.responses import JSONResponse
from tortoise.query_utils import Prefetch
from web3 import AsyncWeb3

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from flow_api import settings
from tortoise import Tortoise
from tortoise.exceptions import DBConnectionError
from flow_api.art_models import Art, ArtCollection, Event, ArtLikes
from services.camunda_service import create_camunda_user
from flow_api.dependencies import (
    sys_key_depends,
    sys_key_or_jwt_depends,
    auth_dependency,
)
from flow_api.flow_models import ExternalWorker, Strategy, Invite, Flow
from flow_api.models import User, TelegramUser, Web3User
from flow_api.rest_models.api_rest_models import (
    UserRest,
    AuthTokenRest,
    UsersLeaderBoardRest,
    ArtLeaderBoardRest,
)
from flow_api.rest_models.art_rest_models import (
    ArtRest,
    ArtCollectionRest,
    EventRest,
    ArtFinanceRest,
)
from flow_api.rest_models.flow_rest_models import (
    ExternalWorkerRest,
    StrategyRest,
    FlowRest,
)
from flow_api.utils import (
    make_update_dict,
    DECORATOR_CACHE_CONFIG,
    create_background_task as _create_background_task,
)

router = APIRouter()

# Configure the cache
# caches.set_config({"default": CACHE_CONFIG})
cache = caches.get("default")
background_tasks = set()
create_background_task = partial(_create_background_task, background_tasks)


def remove_hyphens_from_uuid(uuid_str: str) -> str:
    """Remove hyphens from a UUID string."""
    return uuid_str.replace("-", "")


def add_hyphens_to_uuid(uuid_str: str) -> str:
    """Add hyphens to a UUID string."""
    return re.sub(r"(\w{8})(\w{4})(\w{4})(\w{4})(\w{12})", r"\1-\2-\3-\4-\5", uuid_str)


@router.get("/health_check")
async def health(
        request: Request,
):
    redis_client = request.app.redis
    # Check Redis connection
    try:
        await redis_client.ping()
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Redis connection failed")

    # Check Tortoise ORM (PostgreSQL) connection
    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")
    except DBConnectionError:
        raise HTTPException(status_code=503, detail="PostgreSQL connection failed")



@router.post(
    "/users",
    response_model=UserRest,
    response_model_by_alias=True,
)
async def create_user(
    token: Annotated[str, Depends(sys_key_depends)],
    webapp_user_id: uuid.UUID = Body(None),
    username: str | None = Body(""),
    first_name: str | None = Body(""),
    last_name: str | None = Body(""),
    email: str | None = Body(""),
    language_code: str = Body("en"),
    is_admin: bool = Body(False),
    is_suspicious: bool = Body(False),
    telegram_user_id: int = Body(None),
    discord_user_id: str = Body(None),
    is_block: bool = Body(False),
    is_premium: bool = Body(False),
):
    existing_user = None
    if webapp_user_id:
        existing_user = await User.filter(webapp_user_id=webapp_user_id).first()
    if telegram_user_id:
        existing_user = await User.filter(telegram_user_id=telegram_user_id).first()
    if discord_user_id:
        discord_user_id = await User.filter(discord_user_id=discord_user_id).first()
    if existing_user:
        return JSONResponse({"message": "User already exists"}, status_code=405)
    if not webapp_user_id:
        webapp_user_id = uuid.uuid4()
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
        is_admin=is_admin,
        is_suspicious=is_suspicious,
        telegram_user_id=telegram_user_id,
        discord_user_id=discord_user_id,
        camunda_user_id=None,
        camunda_key=str(uuid.uuid4()),
        webapp_user_id=webapp_user_id,
        is_block=is_block,
        is_premium=is_premium,
        email=email,
    )
    try:
        await user.save()
        tg = None
        if telegram_user_id:
            tg = TelegramUser(
                telegram_id=telegram_user_id,
                is_premium=is_premium,
                user=user,
            )
            await tg.save()
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)

    try:
        user.camunda_user_id = remove_hyphens_from_uuid(str(user.id))
        await create_camunda_user(user)
        await user.save()
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)

    try:
        rest_model = UserRest(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_admin=user.is_admin,
            is_suspicious=user.is_suspicious,
            camunda_user_id=user.camunda_user_id,
            camunda_key=user.camunda_key,
            telegram_user_id=user.telegram_user_id,
            discord_user_id=user.discord_user_id,
            webapp_user_id=user.webapp_user_id,
            is_block=user.is_block,
            is_premium=user.is_premium,
            web3_wallets=[],
        )
        if tg:
            rest_model.telegram_accounts = [tg]
        # await asyncio.gather(
        #     *[
        #         cache.set(f"user_{user_id}", rest_model, ttl=30)
        #         for user_id in [
        #             user.id,
        #             user.webapp_user_id,
        #             user.telegram_user_id,
        #             user.camunda_user_id,
        #         ]
        #         if user_id
        #     ]
        # )
        return rest_model
    except Exception as e:
        await user.delete()
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/users", response_model=UserRest, dependencies=[Depends(sys_key_or_jwt_depends)]
)
async def get_user_by(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    user_id: Optional[UUID4] = Query(None),
    webapp_user_id: Optional[UUID4] = Query(None),
    telegram_user_id: Optional[str] = Query(None),
    discord_user_id: Optional[str] = Query(None),
    camunda_user_id: Optional[str] = Query(None),
):
    if not any(
        [user_id, webapp_user_id, telegram_user_id, camunda_user_id, discord_user_id]
    ):
        raise HTTPException(
            status_code=400,
            detail="Either user_id, webapp_user_id or camunda_user_id must be provided",
        )
    # ids = list(
    #     filter(None, [user_id, webapp_user_id, telegram_user_id, camunda_user_id])
    # )
    # cached_user = await asyncio.gather(
    #     *[cache.get(f"user_{user_id}") for user_id in ids]
    # )
    # if any(cached_user):
    #     return [user for user in cached_user if user][0]
    if user_id:
        user_filter = {"id": user_id}
    elif webapp_user_id:
        user_filter = {"webapp_user_id": webapp_user_id}
    elif camunda_user_id:
        user_filter = {"camunda_user_id": camunda_user_id}
    elif discord_user_id:
        user_filter = {"discord_user_id": discord_user_id}
    else:
        user_filter = {"telegram_user_id": telegram_user_id}
    user = (
        await User.filter(**user_filter)
        .first()
        .prefetch_related(
            "web3_wallets",
            "telegram_accounts",
        )
    )

    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)

    try:
        rest_model = UserRest(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_admin=user.is_admin,
            is_suspicious=user.is_suspicious,
            camunda_user_id=user.camunda_user_id,
            camunda_key=user.camunda_key,
            telegram_user_id=user.telegram_user_id,
            discord_user_id=user.discord_user_id,
            webapp_user_id=user.webapp_user_id,
            is_block=user.is_block,
            is_premium=user.is_premium,
            telegram_accounts=user.telegram_accounts or [],
            web3_wallets=user.web3_wallets or [],
        )
        # await asyncio.gather(
        #     *[
        #         cache.set(f"user_{user_id}", rest_model, ttl=3600)
        #         for user_id in [
        #             user.id,
        #             user.webapp_user_id,
        #             user.telegram_user_id,
        #             user.camunda_user_id,
        #         ]
        #         if user_id
        #     ]
        # )
        return rest_model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/wallets", dependencies=[Depends(sys_key_depends)])
async def get_user_wallet(
    token: Annotated[AuthJWT, Depends(sys_key_depends)],
    user_id: Optional[UUID4] = Query(None),
    webapp_user_id: Optional[UUID4] = Query(None),
    telegram_user_id: Optional[str] = Query(None),
    discord_user_id: Optional[str] = Query(None),
    camunda_user_id: Optional[str] = Query(None),
):
    if user_id:
        user_filter = {"user_id": user_id}
    elif webapp_user_id:
        user_filter = {"user__webapp_user_id": webapp_user_id}
    elif camunda_user_id:
        user_filter = {"user__camunda_user_id": camunda_user_id}
    elif discord_user_id:
        user_filter = {"user__discord_user_id": discord_user_id}
    else:
        user_filter = {"user__telegram_user_id": telegram_user_id}

    wallets = await Web3User().filter(**user_filter)
    return wallets


@router.put(
    "/users",
    response_model=UserRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_user(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    webapp_user_id: uuid.UUID = Body(None),
    camunda_user_id: str = Body(None),
    username: str = Body(None),
    first_name: str = Body(None),
    last_name: str = Body(None),
    email: str = Body(None),
    language_code: str = Body(None),
    is_suspicious: bool = Body(None),
    telegram_user_id: str = Body(None),
    discord_user_id: str = Body(None),
    is_block: bool = Body(None),
    is_premium: bool = Body(None),
    wallet_address: str = Body(None),
    network_type: str = Body("eth"),
    private_key: str = Body(None),
):
    if webapp_user_id:
        user = await User.filter(webapp_user_id=webapp_user_id).first()
    elif camunda_user_id:
        user = await User.filter(camunda_user_id=camunda_user_id).first()
    elif telegram_user_id:
        user = await User.filter(telegram_user_id=telegram_user_id).first()
    elif discord_user_id:
        user = await User.filter(discord_user_id=discord_user_id).first()
    else:
        return JSONResponse({"message": "No user id provided"}, status_code=400)
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)
    update_dict = make_update_dict(
        webapp_user_id=webapp_user_id,
        camunda_user_id=camunda_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        language_code=language_code,
        is_suspicious=is_suspicious,
        telegram_user_id=telegram_user_id,
        is_block=is_block,
        is_premium=is_premium,
    )
    try:
        user = await user.update_from_dict(update_dict)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    if telegram_user_id:
        telegram_user = await TelegramUser.filter(user_id=user.id).first()
        if telegram_user:
            tg = await telegram_user.update_from_dict(update_dict)

        else:
            tg = TelegramUser(telegram_id=telegram_user_id, user=user)
        await tg.save()
    if wallet_address:
        w3_user = Web3User(
            wallet_address=wallet_address,
            network_type=network_type,
            private_key=private_key,
            user=user,
        )
        await w3_user.save()
    user = await User.get(id=user.id).prefetch_related(
        "web3_wallets",
        "telegram_accounts",
    )
    try:
        model = UserRest(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_admin=user.is_admin,
            is_suspicious=user.is_suspicious,
            camunda_user_id=user.camunda_user_id,
            camunda_key=user.camunda_key,
            telegram_user_id=user.telegram_user_id,
            discord_user_id=user.discord_user_id,
            webapp_user_id=user.webapp_user_id,
            is_block=user.is_block,
            is_premium=user.is_premium,
            telegram_accounts=user.telegram_accounts or [],
            web3_wallets=user.web3_wallets or [],
        )
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/login/{webapp_user_id}", response_model=AuthTokenRest)
@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def login(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    webapp_user_id: uuid.UUID = Path(...),
):
    if not webapp_user_id:
        return JSONResponse({"message": "No form data received"}, status_code=400)
    user = await User.filter(webapp_user_id=webapp_user_id).first()
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)
    user_claims = {
        "id": str(user.id),
        "is_admin": user.is_admin,
        "is_suspicious": user.is_suspicious,
        "is_block": user.is_block,
        "is_premium": user.is_premium,
        "webapp_user_id": str(user.webapp_user_id),
        "username": str(user.username),
        "first_name": str(user.first_name),
        "last_name": str(user.last_name),
        "language_code": user.language_code,
        # TODO remove when migrated to JWT on FE
        "camunda_user_id": user.camunda_user_id,
        "camunda_key": str(user.camunda_key),
        "telegram_user_id": user.telegram_user_id,
        "discord_user_id": user.discord_user_id,
    }
    access_token: bytes | str = await auth.create_access_token(
        subject=str(user.id), user_claims=user_claims
    )
    refresh_token: bytes | str = await auth.create_refresh_token(
        subject=str(user.id), user_claims=user_claims
    )

    if isinstance(access_token, bytes):
        access_token = access_token.decode()
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode()
    return AuthTokenRest(access_token=access_token, refresh_token=refresh_token)


@router.get("/refresh", dependencies=[Depends(AuthJWTBearer())])
async def refresh_token(auth: AuthJWT = Depends(AuthJWTBearer())):
    await auth.jwt_refresh_token_required()
    user_id = await auth.get_jwt_subject()
    user_claims = await auth.get_raw_jwt()
    access_token = await auth.create_access_token(
        subject=user_id, user_claims=user_claims
    )
    return {"access_token": access_token}


@router.get(
    "/arts",
    response_model=list[ArtRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=10, **DECORATOR_CACHE_CONFIG)
async def get_arts_sys(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
    parameters: str = Query(..., description="Query parameters as JSON string"),
):
    await token.jwt_optional()
    user_id = await token.get_jwt_subject()
    if parameters:
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            return JSONResponse({"message": "Invalid parameters"}, status_code=400)
        arts = (
            await Art.filter(**params)
            .order_by("-created_at")
            .limit(limit)
            .offset(offset)
            .prefetch_related(
                "likes",
                Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
                "nft_metadata",
            )
        )
    else:
        arts = (
            await Art.all()
            .order_by("-created_at")
            .limit(limit)
            .offset(offset)
            .prefetch_related(
                "likes",
                Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
                "nft_metadata",
            )
        )
    data = [
        ArtRest.parse_obj(
            dict(
                art,
                likes=len(art.likes),
                is_liked=bool(art.liked),
                token_id=art.nft_metadata[0].token_id if art.nft_metadata else None,
                token_address=(
                    art.nft_metadata[0].token_address if art.nft_metadata else None
                ),
            )
        )
        for art in arts
    ]
    return data


@router.post(
    "/art",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_depends)],
)
async def create_art(
    token: Annotated[AuthJWT, Depends(sys_key_depends)],
    name: str | None = Body(None),
    description: str | None = Body(None),
    symbol: str | None = Body(None),
    img_picture: str | None = Body(None),
    description_prompt: str | None = Body(None),
    art_type: str = Body(..., validation_alias="type", alias="type"),
    tags: List[str] = Body([]),
    parent_id: str = Body(None),
    reference_id: str = Body(None),
    camunda_user_id: str = Body(None),
    user_id: str = Body(None),
    webapp_user_id: str = Body(None),
):
    # await auth.jwt_required()
    # user_id = await auth.get_jwt_subject()
    if not user_id:
        if camunda_user_id:
            user = await User.filter(camunda_user_id=camunda_user_id).first()
        elif webapp_user_id:
            user = await User.filter(webapp_user_id=webapp_user_id).first()
        else:
            return {
                "message": "user_id, camunda_user_id or webapp_user_id required"
            }, 404
        if user:
            user_id = user.id
        else:
            raise HTTPException(status_code=404, detail="User not found")
    art_properties = {
        "name": name,
        "description": description,
        "img_picture": img_picture,
        "symbol": symbol,
        "description_prompt": description_prompt,
        "type": art_type,
        "tags": tags,
        "user_id": user_id,
    }
    if reference_id:
        art_properties["reference_id"] = reference_id
    if parent_id:
        art_properties["parent_id"] = parent_id
    art = Art(**art_properties)
    await art.save()
    # try:
    #     create_background_task(art.save())
    # except Exception as e:
    #     return JSONResponse({"error": str(e)}, status_code=400)
    try:
        model = ArtRest.parse_obj(dict(art))
        return model
    except Exception as e:
        create_background_task(art.delete())
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/art/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_art_id(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    art_id: str = Path(...),
):
    user_id = await auth.get_jwt_subject()
    art_id = art_id.strip()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        "nft_metadata",
        "likes",
        Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
    )

    if not art:
        raise HTTPException(status_code=404, detail="Art not found")

    # If nft_metadata is prefetched, it will be in art.nft_metadata
    token_id = None
    token_address = None
    if art.nft_metadata:
        token_id = art.nft_metadata[0].token_id
        token_address = art.nft_metadata[0].token_address

    return ArtRest.parse_obj(
        dict(
            art,
            likes=len(art.likes),
            token_id=token_id,
            token_address=token_address,
            is_liked=bool(art.liked),
        )
    )


@router.post("/art/{art_id}/like", response_model=ArtRest, response_model_by_alias=True)
async def like_art(
    art_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        Prefetch("likes", queryset=ArtLikes.filter(user_id=user_id), to_attr="liked")
    )
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    if art.liked:
        create_background_task(art.liked[0].delete())
        return ArtRest.parse_obj(dict(art, likes=len(art.likes) - 1, is_liked=False))
    create_background_task(ArtLikes(art_id=art_id, user_id=user_id).save())
    return ArtRest.parse_obj(dict(art, likes=len(art.likes) + 1, is_liked=True))


async def fetch_arts(user_id, art_ids):
    if not art_ids:
        return []
    arts = await Art.filter(id__in=art_ids).prefetch_related(
        "nft_metadata",
        "likes",
        Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
    )
    return arts


async def get_random_arts(user_id, count=1, already_shown=None):
    if not already_shown:
        already_shown = set()

    query = Art.filter(
        nft_metadata__token_address__not_isnull=True,
        created_at__gt=(datetime.utcnow() - timedelta(days=7)),
        id__not_in=list(already_shown),
    )

    if user_id is not None:
        query = query.filter(user_id__not=user_id)

    eligible_arts = (
        await query.order_by("-created_at").limit(1000).values_list("id", flat=True)
    )

    if eligible_arts:
        count = min(count, len(eligible_arts))
        random_art_ids = random.sample(eligible_arts, count)
        return random_art_ids

    return []


async def fetch_recommended_art_ids(user_id, already_shown):
    url = f"{settings.WAREHOUSE_URL}/api/queries/48/results"

    if user_id is None:
        return []

    parameters = {"user_id": user_id}
    options = {"max_age": 3600}
    body = {"parameters": parameters, **options}
    headers = {
        "Content-Type": "application/json",
        "Authorization": '5YEugrj2ohASIvK5ocdL54nlSWZ5TOr49WW2oXEu',
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url, headers=headers, data=json.dumps(body), verify_ssl=False
            ) as r:
                r.raise_for_status()
                data = await r.json()

                if data.get("job"):
                    return []
                if data.get("query_result"):
                    query_result = (
                        data.get("query_result", dict())
                        .get("data", dict())
                        .get("rows", [])
                    )
                    return [
                        i["item_id"]
                        for i in query_result
                        if i["item_id"] not in already_shown
                    ]

                logging.error(f"Unexpected warehouse response: {data}")
                return []

    except Exception as e:
        logging.error(
            f"Failed to fetch recommended art for user_id {user_id}. Error: {e}"
        )
        return []


@router.get(
    "/arts/next",
    response_model=List[ArtRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_next_art(
    request: Request,
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    count: int = Query(1, ge=1, le=50),
):
    user_id = await token.get_jwt_subject()
    redis_client = request.app.redis
    already_shown = await redis_client.smembers(f"showed_arts:{user_id}") or set()

    recommended_arts, random_arts = await asyncio.gather(
        fetch_recommended_art_ids(user_id, already_shown),
        get_random_arts(user_id, count, already_shown),
    )

    next_art_ids = (
        recommended_arts[:1] + random_arts[0 : count - len(recommended_arts[:1])]
    )
    next_arts = await fetch_arts(user_id, next_art_ids)

    if not next_arts:
        create_background_task(redis_client.delete(f"showed_arts:{user_id}"))
        recommended_arts, random_arts = await asyncio.gather(
            fetch_recommended_art_ids(user_id, set()),
            get_random_arts(user_id, count, set()),
        )
        next_art_ids = (
            recommended_arts[:1] + random_arts[0 : count - len(recommended_arts[:1])]
        )
        next_arts = await fetch_arts(user_id, next_art_ids)

    arts_response = []

    for art in next_arts:
        token_id = token_address = None
        if art.nft_metadata:
            token_id = art.nft_metadata[0].token_id
            token_address = art.nft_metadata[0].token_address

        arts_response.append(
            ArtRest.parse_obj(
                dict(
                    art,
                    likes=len(art.likes),
                    token_id=token_id,
                    token_address=token_address,
                    is_liked=bool(art.liked),
                )
            )
        )

    # TODO: change usage to zset, so showen items will expire after time
    create_background_task(
        redis_client.sadd(f"showed_arts:{user_id}", *[str(arts_response[0].id)])
    )
    return arts_response


@router.get(
    "/arts/recommended",
    response_model=List[ArtRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_recommended_arts(
    request: Request,
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    count: int = Query(10, ge=1, le=10),
):
    user_id = await token.get_jwt_subject()
    recommended_art_ids = []

    # Few retries for warehouse call, because it may return job before result
    retries = 5
    while retries > 0:
        recommended_art_ids = await fetch_recommended_art_ids(user_id, [])
        if not recommended_art_ids:
            retries -= 1
            await asyncio.sleep(0.1)
            continue
        break

    recommended_arts = []
    if not recommended_art_ids:
        # if no recommendations get random last arts
        recommended_arts = (
            await Art.filter(
                nft_metadata__token_address__not_isnull=True,
                created_at__gt=(datetime.utcnow() - timedelta(days=7)),
            )
            .prefetch_related(
                "nft_metadata",
                "likes",
                Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
            )
            .order_by("-created_at")
            .limit(count)
        )
    else:
        recommended_arts = await fetch_arts(user_id, recommended_art_ids)

    result = []
    for art in recommended_arts:
        token_id = token_address = None
        if art.nft_metadata:
            token_id = art.nft_metadata[0].token_id
            token_address = art.nft_metadata[0].token_address

        result.append(
            ArtRest.parse_obj(
                dict(
                    art,
                    likes=len(art.likes),
                    token_id=token_id,
                    token_address=token_address,
                    is_liked=bool(art.liked),
                )
            )
        )
    return result


@router.get(
    "/arts/history",
    response_model=List[ArtRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_arts_history(
    request: Request,
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    count: int = Query(10, ge=1, le=100),
):
    user_id = await token.get_jwt_subject()
    user = await User.get(id=user_id).prefetch_related("web3_wallets")

    if not user or not user.web3_wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")

    wallet_address = user.web3_wallets[0].wallet_address
    async with httpx.AsyncClient() as client:
        env = "stage"
        if settings.ENVIRONMENT in (
            "stage",
            "prod",
        ):
            env = settings.ENVIRONMENT
        response = await client.post(
            "https://api-gurunetwork-wh.dex.guru/wh/last_arts_history_by_wallet",
            json={
                "parameters": {
                    "limit": str(count),
                    "env": env,
                    "wallet_address": wallet_address,
                }
            },
            headers={"Content-Type": "application/json"},
            params={"api_key": "z5spwLUMRg8yGE9UmRnuYq7Qx4S8jq3Uf3njHYv5"},
        )

        response.raise_for_status()

        last_art_ids = [i["art_id"] for i in response.json()]

    arts = await fetch_arts(user_id, last_art_ids)
    result = []
    for art in arts:
        token_id = token_address = None
        if art.nft_metadata:
            token_id = art.nft_metadata[0].token_id
            token_address = art.nft_metadata[0].token_address

        result.append(
            ArtRest.parse_obj(
                dict(
                    art,
                    likes=len(art.likes),
                    token_id=token_id,
                    token_address=token_address,
                    is_liked=bool(art.liked),
                )
            )
        )
    return result


@router.get(
    "/arts/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_arts_id(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    art_id: str = Path(...),
):
    user_id = await token.get_jwt_subject()
    art_id = art_id.strip()
    art = await Art.get_or_none(id=art_id).prefetch_related(
        "nft_metadata",
        "likes",
        Prefetch("likes", ArtLikes.filter(user_id=user_id), to_attr="liked"),
    )

    if not art:
        raise HTTPException(status_code=404, detail="Art not found")

    # If nft_metadata is prefetched, it will be in art.nft_metadata
    token_id = None
    token_address = None
    nft_token_address = None
    if art.nft_metadata:
        for item in art.nft_metadata:
            if item.token_id == 0:
                token_address = item.token_address
            else:
                nft_token_address = item.token_address
                token_id = item.token_id

    return ArtRest.parse_obj(
        dict(
            art,
            likes=len(art.likes),
            token_id=token_id,
            token_address=token_address,
            is_liked=bool(art.liked),
            nft_token_address=nft_token_address,
        )
    )


@router.put(
    "/art/{art_id}",
    response_model=ArtRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_art(
    token: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    art_id: str = Path(...),
    name: str | None = Body(None),
    description: str | None = Body(None),
    img_picture: str | None = Body(None),
    symbol: str | None = Body(None),
    description_prompt: str | None = Body(None),
    art_type: str = Body(..., validation_alias="type", alias="type"),
    tags: List[str] = Body(None),
    parent_id: str | None = Body(None),
    reference_id: str | None = Body(None),
):
    art = await Art.filter(id=art_id).first()
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        description_prompt=description_prompt,
        type=art_type,
        tags=tags,
        parent_id=parent_id,
        reference_id=reference_id,
        symbol=symbol,
    )
    try:
        art = await art.update_from_dict(update_dict)
        art.created_at = (
            art.created_at.replace(tzinfo=None)
            if art.created_at.tzinfo
            else art.created_at
        )
        await art.save()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    try:
        model = ArtRest.parse_obj(dict(art))
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.delete(
    "/art/{art_id}",
    dependencies=[Depends(AuthJWTBearer())],
)
async def delete_external_worker(
    art_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()

    art = await Art.filter(user_id=user_id, id=art_id).first()
    if not art:
        return JSONResponse({"message": "Art not found"}, status_code=404)
    await art.delete()
    return JSONResponse({"message": "Art deleted"}, status_code=200)


@router.get(
    "/art_collection",
    response_model=list[ArtCollectionRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_collections(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    parent_id: str | None = Query(None),
    limit: int = 10,
    offset: int = 0,
):
    if parent_id:
        art_collections = await ArtCollection.filter(parent_id=parent_id).limit(limit).offset(offset)
    else:
        art_collections = await ArtCollection.all().limit(limit).offset(offset)
    return [
        ArtCollectionRest.model_validate(art_collection)
        for art_collection in art_collections
    ]


@router.post(
    "/art_collection",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def create_collection(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    symbol: str = Body(...),
    base_uri: str | None = Body(None),
    address: str | None = Body(None),
    parent_id: str | None = Body(None),
    arts: List = Body([]),
    collection_type: str = Body(..., validation_alias="type", alias="type"),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    new_strategy = ArtCollection(
        name=name,
        user_id=user_id,
        base_uri=base_uri,
        address=address,
        parent_id=parent_id,
        symbol=symbol,
        arts=arts,
        type=collection_type,
    )
    try:
        model = ArtCollectionRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/art_collection/{collection_id}",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_collection(
    collection_id: str = Path(...), auth: AuthJWT = Depends(sys_key_or_jwt_depends)
):
    collection = await ArtCollection.filter(id=collection_id).first()
    if not collection:
        return JSONResponse({"message": "collection not found"}, status_code=404)
    return ArtCollectionRest.model_validate(collection)


@router.put(
    "/art_collection/{collection_id}",
    response_model=ArtCollectionRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def update_collection(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    collection_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_event_cover: str = Body(None),
    collection_type: str = Body(None, validation_alias="type", alias="type"),
    address: str = Body(None),
    parent_id: str = Body(None),
    collections: dict = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_collection = await ArtCollection.filter(
        user_id=user_id, id=collection_id
    ).first()
    if not art_collection:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_event_cover=img_event_cover,
        type=collection_type,
        address=address,
        parent_id=parent_id,
        reference_id=reference_id,
        collections=collections,
    )
    update_art_collection = await art_collection.update_from_dict(update_dict)
    model = ArtCollectionRest.model_validate(update_art_collection)
    await update_art_collection.save()
    return model


@router.delete(
    "/art_collection/{collection_id}", dependencies=[Depends(AuthJWTBearer())]
)
async def delete_collection(
    collection_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_collection = await ArtCollection.filter(
        user_id=user_id, id=collection_id
    ).first()
    if not art_collection:
        return JSONResponse({"message": "Art Collection not found"}, status_code=404)
    await art_collection.delete()
    return JSONResponse({"message": "Art Collection deleted"}, status_code=200)


@router.get(
    "/event",
    response_model=list[EventRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_collections(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    limit: int = 10,
    offset: int = 0,
):
    event_collections = await Event.all().limit(limit).offset(offset)
    return [
        EventRest.model_validate(event_collection)
        for event_collection in event_collections
    ]


@router.post(
    "/event",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def create_event(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    description: str = Body(...),
    address: str | None = Body(None),
    location: str | None = Body(None),
    img_event_cover: str | None = Body(None),
    collections: dict | None = Body(None),
    event_type: str = Body(..., validation_alias="type", alias="type"),
    reference_id: str | None = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    new_strategy = Event(
        name=name,
        user_id=user_id,
        description=description,
        address=address,
        location=location,
        img_event_cover=img_event_cover,
        collections=collections,
        type=event_type,
        reference_id=reference_id,
    )
    try:
        model = EventRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/event/{event_id}",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_event(event_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    event = await Event.filter(user_id=user_id, id=event_id).first()
    return EventRest.model_validate(event)


@router.put(
    "/event/{event_id}",
    response_model=EventRest,
    response_model_by_alias=True,
    dependencies=[Depends(AuthJWTBearer())],
)
async def update_event(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    event_id: str = Path(...),
    name: str = Body(...),
    description: str = Body(...),
    address: str | None = Body(None),
    location: str | None = Body(None),
    img_event_cover: str | None = Body(None),
    collections: dict | None = Body(None),
    event_type: str = Body(..., validation_alias="type", alias="type"),
    reference_id: str | None = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_event = await Event.filter(user_id=user_id, id=event_id).first()
    if not art_event:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        user_id=user_id,
        description=description,
        address=address,
        location=location,
        img_event_cover=img_event_cover,
        collections=collections,
        type=event_type,
        reference_id=reference_id,
    )
    update_art_event = await art_event.update_from_dict(update_dict)
    model = EventRest.model_validate(update_art_event)
    await update_art_event.save()
    return model


@router.delete("/art/event/{event_id}", dependencies=[Depends(AuthJWTBearer())])
async def delete_event(
    event_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    art_event = await Event.filter(user_id=user_id, id=event_id).first()
    if not art_event:
        return JSONResponse({"message": "Art Collection not found"}, status_code=404)
    await art_event.delete()
    return JSONResponse({"message": "Art Collection deleted"}, status_code=200)


@router.get(
    "/external_workers",
    response_model=list[ExternalWorkerRest],
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_external_workers(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    limit: int = 10,
    offset: int = 0,
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_workers = (
        await ExternalWorker.filter(user_id=user_id).limit(limit).offset(offset)
    )
    return [
        ExternalWorkerRest.model_validate(external_worker)
        for external_worker in external_workers
    ]


@router.post(
    "/external_workers",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def create_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    name: str = Body(...),
    description: str = Body(...),
    external_worker_type: str = Body(..., validation_alias="type", alias="type"),
    img_picture: str | None = Body(None),
    schema: dict | None = Body(None),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    new_external_worker = ExternalWorker(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        schema=schema,
        type=external_worker_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    model = ExternalWorkerRest.model_validate(new_external_worker)
    await new_external_worker.save()
    return model


@router.get(
    "/external_workers/{external_worker_id}",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    external_worker_id: str = Path(...),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    return ExternalWorkerRest.model_validate(external_worker)


@router.put(
    "/external_workers/{external_worker_id}",
    response_model=ExternalWorkerRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def update_external_worker(
    auth: AuthJWT = Depends(AuthJWTBearer()),
    external_worker_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    schema: dict = Body(None),
    img_picture: str = Body(None),
    external_worker_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    if not external_worker:
        return JSONResponse({"message": "External worker not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=external_worker_type,
        parent_id=parent_id,
        reference_id=reference_id,
        schema=schema,
    )
    try:
        updated_worker = await external_worker.update_from_dict(update_dict)
        model = ExternalWorkerRest.model_validate(updated_worker)
        await updated_worker.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.delete(
    "/external_workers/{external_worker_id}",
    dependencies=[Depends(auth_dependency)],
)
async def delete_external_worker(
    external_worker_id: str = Path(...), auth: AuthJWT = Depends(AuthJWTBearer())
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()

    external_worker = await ExternalWorker.filter(
        user_id=user_id, id=external_worker_id
    ).first()
    if not external_worker:
        return JSONResponse({"message": "External worker not found"}, status_code=404)
    await external_worker.delete()
    return JSONResponse({"message": "External worker deleted"}, status_code=200)


@router.get(
    "/strategy",
    response_model=list[StrategyRest],
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_strategies(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
):
    strategies = await Strategy.all().limit(limit).offset(offset)
    return [StrategyRest.model_validate(strategy) for strategy in strategies]


@router.get(
    "/flows",
    response_model=list[FlowRest],
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_flows(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    limit: int = 10,
    offset: int = 0,
):
    flows = await Flow.all().limit(limit).offset(offset)
    return [FlowRest.model_validate(flow) for flow in flows]


@router.get(
    "/flow/{flow_id}",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_flow(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    flow_id: str = Path(...),
):
    flow = await Flow.filter(id=flow_id).first()
    return FlowRest.model_validate(flow)


@router.put(
    "/flow/{flow_id}",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_flow(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    flow_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_picture: str = Body(None),
    flow_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
    reward: int = Body(0),
):
    flow = await Flow.filter(id=flow_id).first()
    if not flow:
        return JSONResponse({"message": "Flow not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=flow_type,
        parent_id=parent_id,
        reference_id=reference_id,
        reward=reward,
    )
    updated_flow = await flow.update_from_dict(update_dict)
    model = FlowRest.model_validate(flow)
    await updated_flow.save()
    return model


@router.delete("/flow/{flow_id}", dependencies=[Depends(auth_dependency)])
async def delete_flow(
    flow_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    flow = await Flow.filter(user_id=user_id, id=flow_id).first()
    if not flow:
        return JSONResponse({"message": "Flow not found"}, status_code=404)
    await flow.delete()
    return JSONResponse({"message": "Flow deleted"}, status_code=200)


@router.post(
    "/flow",
    response_model=FlowRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def create_flow(
    auth: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    reference_id: str | None = Body(None),
    parent_id: str | None = Body(None),
    user_id: str | None = Body(None),
    name: str = Body(...),
    description: str = Body(...),
    img_picture: str | None = Body(None),
    flow_type: str = Body(..., validation_alias="type", alias="type"),
):
    if not user_id:
        user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    if not parent_id:
        parent_id = user_id
    new_flow = Flow(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        type=flow_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    try:
        model = FlowRest.model_validate(new_flow)
        await new_flow.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post(
    "/strategy",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(auth_dependency)],
)
async def create_strategy(
    auth: Annotated[AuthJWT, Depends(sys_key_or_jwt_depends)],
    reference_id: str | None = Body(None),
    parent_id: str | None = Body(None),
    user_id: str | None = Body(None),
    name: str = Body(...),
    description: str = Body(...),
    img_picture: str | None = Body(None),
    schema: dict | None = Body(None),
    strategy_type: str = Body(..., validation_alias="type", alias="type"),
):
    # TODO: here there is an issue if user loggined through GPT he can specify othe user_id and p[ost from him, need to fix
    if not user_id:
        user_id = await auth.get_jwt_subject()
    if not reference_id:
        reference_id = user_id
    if not parent_id:
        parent_id = user_id
    new_strategy = Strategy(
        name=name,
        user_id=user_id,
        description=description,
        img_picture=img_picture,
        schema=schema,
        type=strategy_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    try:
        model = StrategyRest.model_validate(new_strategy)
        await new_strategy.save()
        return model
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get(
    "/strategy/{strategy_id}",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=300, **DECORATOR_CACHE_CONFIG)
async def get_strategy(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    strategy_id: str = Path(...),
):
    strategy = await Strategy.filter(id=strategy_id).first()
    return StrategyRest.model_validate(strategy)


@router.put(
    "/strategy/{strategy_id}",
    response_model=StrategyRest,
    response_model_by_alias=True,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def update_strategy(
    auth: Annotated[bool, Depends(sys_key_or_jwt_depends)],
    strategy_id: str = Path(...),
    name: str = Body(None),
    description: str = Body(None),
    img_picture: str = Body(None),
    strategy_type: str = Body(None, validation_alias="type", alias="type"),
    parent_id: int = Body(None),
    reference_id: int = Body(None),
):
    strategy = await Strategy.filter(id=strategy_id).first()
    if not strategy:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    update_dict = make_update_dict(
        name=name,
        description=description,
        img_picture=img_picture,
        type=strategy_type,
        parent_id=parent_id,
        reference_id=reference_id,
    )
    updated_strategy = await strategy.update_from_dict(update_dict)
    model = StrategyRest.model_validate(strategy)
    await updated_strategy.save()
    return model


@router.delete("/strategy/{strategy_id}", dependencies=[Depends(auth_dependency)])
async def delete_strategy(
    strategy_id: str = Path(...),
    auth: AuthJWT = Depends(AuthJWTBearer()),
):
    await auth.jwt_required()
    user_id = await auth.get_jwt_subject()
    strategy = await Strategy.filter(user_id=user_id, id=strategy_id).first()
    if not strategy:
        return JSONResponse({"message": "Strategy not found"}, status_code=404)
    await strategy.delete()
    return JSONResponse({"message": "Strategy deleted"}, status_code=200)


@router.post(
    "/invites/chain/{chain_id}/token/{token_id}",
    include_in_schema=False,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def invite_user(
    chain_id: int = Path(...),
    token_id: int = Path(...),
    wallet_address: str = Body(),
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    if not await Invite.filter(wallet_address=wallet_address):
        invite = Invite(
            token_id=token_id, chain_id=chain_id, wallet_address=wallet_address.lower()
        )
        await invite.save()
        return JSONResponse({"id": str(invite.id)}, status_code=200)
    return JSONResponse({"message": "User already invited"}, status_code=200)


@router.post(
    "/invites/chain/{chain_id}",
    include_in_schema=False,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def mark_users_as_updated(
    chain_id: int = Path(...),
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
):
    updated = []
    invites = await Invite.filter(chain_id=chain_id, is_updated_merkle_root=False).all()
    for invite in invites:
        invite.is_updated_merkle_root = True
        updated.append(invite)
    await Invite.bulk_update(
        updated, fields=["id", "is_updated_merkle_root"], batch_size=1000
    )
    return JSONResponse({"message": "Users marked as updated"}, status_code=200)


@router.get(
    "/invites/chain/{chain_id}",
)
@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_invited_wallets(
    auth: AuthJWT = Depends(sys_key_depends),
    chain_id: int = Path(...),
    only_updated: bool = Query(True),
) -> list[str]:
    if only_updated:
        invites = await Invite.filter(chain_id=chain_id, is_updated_merkle_root=True)
    else:
        invites = await Invite.filter(chain_id=chain_id)
    return list({invite.wallet_address.lower() for invite in invites})


@router.get(
    "/invites/chain/{chain_id}/token/{token_id}",
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
@cached(ttl=5, **DECORATOR_CACHE_CONFIG)
async def get_invited_wallets_by_token_id(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    chain_id: int = Path(...),
    token_id: int = Path(...),
) -> list[str]:
    invites = await Invite.filter(token_id=token_id, chain_id=chain_id)
    return [invite.wallet_address for invite in invites]


@router.get(
    "/finance/arts",
    dependencies=[Depends(sys_key_or_jwt_depends)],
    response_model=list[ArtFinanceRest],
)
async def get_art_finance(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    token_addresses: str = Query(...),
):
    w3 = AsyncWeb3(
        AsyncWeb3.AsyncHTTPProvider("https://rpc-testnet-0f871sgqn2.t.conduit.xyz")
    )
    with open(pathlib.Path(__file__).parent.parent / "BurningMemeBetABI.json") as f:
        contract_abi = json.load(f)
    rest_data = []
    http_client = httpx.AsyncClient()
    for token_address in token_addresses.split(","):
        address = w3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=address, abi=contract_abi)
        burn_total_supply, mint_total_supply, balance, voting_end_ts, participants = (
            await asyncio.gather(
                contract.functions.burnTotalSupply().call(),
                contract.functions.mintTotalSupply().call(),
                w3.eth.get_balance(address),
                contract.functions.getBettingEndTimestamp().call(),
                http_client.post(
                    "https://api-gurunetwork-wh.dex.guru/wh/meme_participants_count",
                    json={
                        "parameters": {"token_address": token_address},
                    },
                    headers={"Content-Type": "application/json"},
                    params={"api_key": "fXIt640X4DfIULCmIfsgBJe5AGi8BPLcys0opTGc"},
                ),
            )
        )
        try:
            participants.raise_for_status()
            participants = participants.json()[0]["participants"]
        except Exception as e:
            participants = 0
        rest_data.append(
            ArtFinanceRest(
                burn_total_supply=burn_total_supply,
                mint_total_supply=mint_total_supply,
                guru_balance=balance / 10**18,
                token_address=token_address,
                total_supply=burn_total_supply + mint_total_supply,
                voting_end_timestamp=voting_end_ts,
                participants=participants,
            )
        )
    return rest_data


@router.get(
    "/leaderboard/users",
    response_model=list[UsersLeaderBoardRest],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_top_locked_burns(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    limit: int = Query(1000),
):
    cache_key = f"leaderboard-users-limit-{limit}"
    try:
        cached_result = await cache.get(cache_key)
        if cached_result:
            return cached_result
    except ConnectionError:
        logging.error(f"Redis connection error get key {cache_key}")

    url = f"{settings.WAREHOUSE_URL}/api/queries/24/results"

    env = "stage"
    if settings.ENVIRONMENT in (
        "stage",
        "prod",
    ):
        env = settings.ENVIRONMENT

    parameters = {"limit": str(limit), "env": env}
    options = {"max_age": 3600}
    body = {"parameters": parameters, **options}
    headers = {
        "Content-Type": "application/json",
        "Authorization": "K4LQqepyRumnSRPmliUPPJMnTbK7x3FpRKxeFRn0",
    }
    retries = 5
    async with httpx.AsyncClient() as client:
        while retries:
            response = await client.post(
                url,
                json=body,
                headers=headers,
            )
            retries -= 1
            if response.status_code >= 400:
                await asyncio.sleep(1)
                continue
            data = response.json()
            if isinstance(data, dict) and data.get("job"):
                await asyncio.sleep(1)
                continue
            if isinstance(data, dict) and data.get("query_result"):
                data = data.get("query_result", {}).get("data", {}).get("rows", [])
                await cache.set(cache_key, data, ttl=3600)
                return data
    return []


@router.get(
    "/leaderboard/users/{wallet_address}",
    response_model=UsersLeaderBoardRest,
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_user_locked_burns(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    wallet_address: str = Path(...),
):
    cache_key = f"leaderboard-users-{wallet_address}"
    try:
        cached_result = await cache.get(cache_key)
        if cached_result:
            return cached_result
    except ConnectionError:
        logging.error(f"Redis connection error get key {cache_key}")

    env = "stage"
    if settings.ENVIRONMENT in (
        "stage",
        "prod",
    ):
        env = settings.ENVIRONMENT

    url = f"{settings.WAREHOUSE_URL}/api/queries/39/results"

    parameters = {"target_wallet_address": wallet_address.lower(), "env": env}
    options = {"max_age": 3600}
    body = {"parameters": parameters, **options}
    headers = {
        "Content-Type": "application/json",
        "Authorization": "o8Y5MjYV2P74mgi0EIyD9sKGyeHGLhm0RVT87tOM",
    }
    retries = 10
    data = None
    async with httpx.AsyncClient() as client:
        while retries:
            response = await client.post(
                url,
                json=body,
                headers=headers,
            )
            retries -= 1
            if response.status_code >= 400:
                await asyncio.sleep(1)
                continue
            data = response.json()
            if isinstance(data, dict) and data.get("job"):
                await asyncio.sleep(1)
                continue
            if isinstance(data, dict) and data.get("query_result"):
                data = data.get("query_result", {}).get("data", {}).get("rows", [])
                if data:
                    await cache.set(cache_key, data[0], ttl=300)
                    return data[0]

    raise HTTPException(status_code=404, detail="not found")


@router.get(
    "/leaderboard/arts",
    response_model=list[ArtLeaderBoardRest],
    dependencies=[Depends(sys_key_or_jwt_depends)],
)
async def get_top_arts(
    auth: AuthJWT = Depends(sys_key_or_jwt_depends),
    limit: int = Query(1000),
):
    # Step 1: Fetch top tokens from the external API (financial data)
    cache_key = f"leaderboard-arts-limit-{limit}"
    try:
        cached_res = await cache.get(cache_key)
        if cached_res:
            return cached_res
    except ConnectionError:
        logging.error(f"Redis connection error get key {cache_key}")

    env = "prod"
    if settings.ENVIRONMENT in (
        "stage",
        "prod",
    ):
        env = settings.ENVIRONMENT

    url = f"{settings.WAREHOUSE_URL}/api/queries/25/results"
    parameters = {"limit": str(limit), "env": env}
    options = {"max_age": 3600}
    body = {"parameters": parameters, **options}
    headers = {
        "Content-Type": "application/json",
        "Authorization": "JeoxwEqnvswepKmCubVdgyGmPJAaYWlBd7mIsekR",
    }

    retries = 5
    data = []
    async with httpx.AsyncClient() as client:
        while retries:
            response = await client.post(
                url,
                json=body,
                headers=headers,
            )
            retries -= 1
            if response.status_code >= 400:
                await asyncio.sleep(1)
                continue
            data = response.json()
            if isinstance(data, dict) and data.get("job"):
                await asyncio.sleep(1)
                continue
            if isinstance(data, dict) and data.get("query_result"):
                data = data.get("query_result", {}).get("data", {}).get("rows", [])
                await cache.set(cache_key, data, ttl=3600)

    top_tokens = data

    # Step 2: Create a list of token_addresses
    token_addresses = list(token["token_address"] for token in top_tokens)

    # Step 3: Fetch arts by token_address
    arts = await Art.filter(
        nft_metadata__token_address__in=token_addresses
    ).prefetch_related("nft_metadata")

    # Step 5: Create a dictionary mapping token_address to art
    rest = []
    for token in top_tokens:
        for i, art in enumerate(arts):
            if art.nft_metadata[0].token_address != token["token_address"]:
                continue
            rest.append(ArtLeaderBoardRest(**token, art=ArtRest(**dict(art))))
            del arts[i]
            break
    await cache.set(cache_key, rest, ttl=3600)
    return rest
