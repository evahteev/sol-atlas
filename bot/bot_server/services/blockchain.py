from pathlib import Path

from aiocache import cached
from web3 import AsyncWeb3, AsyncHTTPProvider

from bot_server.core.config import settings

w3 = AsyncWeb3(AsyncHTTPProvider(settings.WEB3_PROVIDER))
with open(Path(__file__).parent / "BurningMemeBetABI.json") as f:
    BURNING_MEME_ABI = f.read()


async def get_balance(address: str) -> int:
    return await w3.eth.get_balance(w3.to_checksum_address(address))


def get_burning_meme_contract(token_address: str):
    return w3.eth.contract(
        address=w3.to_checksum_address(token_address), abi=BURNING_MEME_ABI
    )


async def get_burn_total_supply(token_address: str):
    if not token_address:
        return 0
    contract = get_burning_meme_contract(token_address)
    return await contract.functions.burnTotalSupply().call()


async def get_mint_total_supply(token_address: str):
    if not token_address:
        return 0
    contract = get_burning_meme_contract(token_address)
    return await contract.functions.mintTotalSupply().call()


@cached(ttl=7*24*60*60)
async def get_voting_end_timestamp(token_address: str):
    if not token_address:
        return 0
    contract = get_burning_meme_contract(token_address)
    return await contract.functions.getBettingEndTimestamp().call()
