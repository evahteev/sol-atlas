import { useQuery } from '@tanstack/react-query'

import { FlowClientObject } from '../..'
import { components } from '../../schema'

export const useFlows = () => {
  return useQuery({
    queryKey: ['FlowClientObject.flows.list'],
    queryFn: () => FlowClientObject.flows.list(),
  })
}

export function useCollection(collectionId: string) {
  return useQuery({
    queryKey: ['FlowClientObject.arts.collection', collectionId],
    queryFn: async () => {
      const result = await FlowClientObject.arts.collection(collectionId)

      return result
    },
  })
}

export function useArtsByCollection(collectionId: string) {
  return useQuery({
    queryKey: ['FlowClientObject.arts.collection', collectionId],
    queryFn: async () => {
      const collection = await FlowClientObject.arts.collection(collectionId)
      const artIds = collection?.arts

      if (!artIds) {
        return null
      }

      const arts: components['schemas']['ArtRest'][] = []
      await Promise.all(
        artIds.map(async (artId) => {
          const art = await FlowClientObject.arts
            .get(artId as string)

            .catch((e) => {
              console.log(e)
              return undefined
            })

          if (art) {
            arts.push(art)
          }
        })
      )
      arts.sort((a, b) =>
        a.created_at && b.created_at
          ? new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          : -1
      )

      return arts
    },
  })
}

export function useArt(artId: string) {
  return useQuery({
    queryKey: ['FlowClientObject.arts.get', artId],
    queryFn: () => FlowClientObject.arts.get(artId),
  })
}

export function useArts(query?: string) {
  return useQuery({
    queryKey: ['FlowClientObject.arts.list', query],
    queryFn: () => FlowClientObject.arts.list(query),
  })
}

export function useArtNext({
  count,
  initialData,
}: {
  count?: number
  initialData?: components['schemas']['ArtRest'][]
}) {
  return useQuery({
    initialData,
    queryKey: ['FlowClientObject.arts.next', count],
    queryFn: () => FlowClientObject.arts.next(count),
  })
}

export function useArtRecommended({
  count,
  initialData,
}: {
  count?: number
  initialData?: components['schemas']['ArtRest'][]
}) {
  return useQuery({
    initialData,
    queryKey: ['FlowClientObject.arts.recommended', count],
    queryFn: () => FlowClientObject.arts.recommended(count),
  })
}

export function useArtNextWithVote(
  initialData?: components['schemas']['ArtRest'][],
  userId?: string
) {
  return useQuery({
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    initialData,
    queryKey: ['FlowClientObject.arts.next with vote', userId, initialData],
    queryFn: async () => {
      const arts = await FlowClientObject.arts.next()
      if (!userId) {
        console.error("Can't initiate vote. No session found")
        return arts
      }
      arts.map((art) => {
        FlowClientObject.engine.process.definitions
          .start('meme_voting', {
            business_key: `${userId}:${art?.id}`,
            variables: {
              gen_art_id: {
                type: 'string',
                value: art?.id,
              },
              vote_duration: {
                type: 'string',
                value: 'PT10080M',
              },
            },
          })
          .then(console.log)
      })
      return arts
    },
  })
}

export function useRandomArt() {
  return useQuery({
    queryKey: ['FlowClientObject.arts.get'],
    queryFn: async () => {
      const arts = await FlowClientObject.arts.list()
      return arts[Math.floor(Math.random() * 9)]
    },
  })
}

export function useArtFinance({
  token_addresses,
  initialData,
}: {
  token_addresses?: string[]
  initialData?: components['schemas']['ArtFinanceRest'][]
}) {
  return useQuery({
    initialData,
    queryKey: ['FlowClientObject.arts.finances', token_addresses],
    queryFn: () => FlowClientObject.arts.finances(token_addresses),
  })
}

export function useTopUsers() {
  return useQuery({
    queryKey: ['FlowClientObject.leaderboard.users.list'],
    queryFn: async () => FlowClientObject.leaderboard.users.list(),
  })
}

export function useMyTopUser(walletAddress?: string) {
  return useQuery({
    queryKey: ['FlowClientObject.leaderboard.users.get', walletAddress],
    queryFn: async () => walletAddress && FlowClientObject.leaderboard.users.get(walletAddress),
  })
}

export function useTopArts() {
  return useQuery({
    queryKey: ['FlowClientObject.leaderboard.arts.list'],
    queryFn: async () => FlowClientObject.leaderboard.arts.list(),
  })
}
