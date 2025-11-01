import { TokenCoingeckoData } from '@/models/coingecko'
import { coingeckoApiPlatformIds } from '@/models/coingecko'

const coingeckoAPIUrl = 'https://api.coingecko.com/api/v3'
export async function fetchTokenCoinGeckoData(address: string, network: string) {
  const platformId = coingeckoApiPlatformIds[network.toLowerCase()]

  if (!platformId) {
    return null
  }

  return fetch(`${coingeckoAPIUrl}/coins/${platformId}/contract/${address.toLowerCase()}`, {
    next: {
      revalidate: 12 * 60 * 60,
      tags: ['all', 'fetch', 'fetchTokenCoinGeckoData'],
    },
  })
}
export async function getTokenCoinGeckoData(
  address: string,
  network: string
): Promise<TokenCoingeckoData | null> {
  return (
    (await fetchTokenCoinGeckoData(address, network)
      ?.then((res) => res?.json())
      .catch(() => null)) ?? null
  )
}
