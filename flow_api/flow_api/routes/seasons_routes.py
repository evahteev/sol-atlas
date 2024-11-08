import pathlib

from aiocache import cached
from fastapi import APIRouter, Path, Depends, Query
from starlette.responses import JSONResponse, Response

from async_fastapi_jwt_auth import AuthJWT
from flow_api.dependencies import sys_key_depends
from flow_api.flow_models import NftMetadata
from flow_api.utils import DECORATOR_CACHE_CONFIG

seasons_router = APIRouter()


@seasons_router.get(
    "/{season_id}/{token_id}",
)
@cached(ttl=3600, **DECORATOR_CACHE_CONFIG)
async def get_nft_metadata_mainnet(
    season_id: str = Path(...),
    token_id: str = Path(...),
):
    metadata = {
        "description": f"Guru Network Invite num. {token_id}",  # we can add promt
        "external_url": "https://gurunetwork.ai",
        "image": f"https://flow.gurunetwork.ai/seasons/{season_id}/chain/1/token/{token_id}/img.jpeg",
        "name": "Dex Guru Season 2 Invite",
        # "attributes": [...],
    }
    return JSONResponse(metadata, status_code=200)


@seasons_router.get(
    "/{season_id}/chain/{chain_id}/token/{token_id}/img.jpeg",
)
@cached(ttl=3600, **DECORATOR_CACHE_CONFIG)
async def get_nft_picture(
    season_id: str = Path(...),
    chain_id: str = Path(...),
    token_id: str = Path(...),
):
    with open(pathlib.Path(__file__).parent.parent / "nft_example.jpeg", "rb") as file:
        img = file.read()
    return Response(content=img, media_type="image/jpeg")


@seasons_router.get(
    "/{season_id}/chain/{chain_id}/{token_id}",
)
async def get_nft_metadata(
    season_id: str = Path(...),
    chain_id: str = Path(...),
    token_id: str = Path(...),
):
    image = (
        await NftMetadata.filter(
            season_id=season_id, chain_id=chain_id, token_id=token_id
        )
        .prefetch_related("art")
        .first()
    )
    if image:
        img_url = image.art.img_picture
        description = image.art.description
        name = image.art.name
    else:
        img_url = f"https://flow.gurunetwork.ai/seasons/{season_id}/chain/{chain_id}/token/{token_id}/img.jpeg"
        description = "Dex Guru Season 2 Invite"
        name = "Dex Guru Season 2 Invite"
    metadata = {
        "description": description,
        "external_url": "https://gurunetwork.ai",
        "image": img_url,
        "name": name,
        # "attributes": [...],
    }
    return JSONResponse(metadata, status_code=200)


@seasons_router.post(
    "/{season_id}/chain/{chain_id}/token/{token_id}/art/{art_id}",
    dependencies=[Depends(sys_key_depends)],
)
async def store_nft_metadata(
    auth: AuthJWT = Depends(sys_key_depends),
    season_id: str = Path(...),
    chain_id: str = Path(...),
    token_id: str = Path(...),
    art_id: str = Path(...),
    token_address: str = Query(""),
):
    exist = await NftMetadata.filter(
        season_id=season_id,
        chain_id=chain_id,
        token_id=token_id,
        art_id=art_id,
        token_address=token_address,
    ).first()
    if exist:
        return JSONResponse({"message": "Metadata already stored"}, status_code=200)
    await NftMetadata(
        season_id=season_id,
        chain_id=chain_id,
        token_id=token_id,
        art_id=art_id,
        token_address=token_address,
    ).save()
    return JSONResponse({"message": "Metadata stored"}, status_code=200)
