'use client'

import { FC, useEffect, useState } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'
import useWebSocket, { ReadyState } from 'react-use-websocket'
import { useWillUnmount } from 'rooks'

import { TokensExplorerContent } from '@/app/[locale]/(default)/tokens/(default)/_components/content/content'
import Delta from '@/components/atoms/Delta'
import TokenAsset from '@/components/atoms/TokenAsset'
import Value from '@/components/atoms/Value'
import Dialog from '@/components/ui/Dialog'
import { TokenHistoryCandle } from '@/models/candle'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { formatNumber, getPreviousPriceByDelta } from '@/utils/numbers'
import { getTokenPriceChannel } from '@/utils/tokens'

import styles from './asset.module.scss'

type PageTokenAssetProps = {
  className?: string
  token: TokenV3Model
  chains: ChainModel[]
}

export const PageTokenAsset: FC<PageTokenAssetProps> = ({ className, token, chains }) => {
  const [isOpen, setIsOpen] = useState(false)
  const price24hAgo = getPreviousPriceByDelta(token.priceUSD, token.priceUSDChange24h)
  const [currentPriceData, setCurrentPriceData] = useState<{ price: number; delta: number }>({
    price: token.priceUSD,
    delta: token.priceUSDChange24h * 100,
  })

  const channelId = getTokenPriceChannel(token.id, 60, chains)

  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket<{
    type: string
    data: { update?: TokenHistoryCandle }
  }>(`${env('NEXT_PUBLIC_CHANNELS_WS_API')}`, {
    shouldReconnect: () => true,
    share: true,
    filter: (message) => {
      const data = JSON.parse(message.data)
      return data.type === 'updated' && data.data.channel_id === channelId
    },
  })

  const isConnected = readyState === ReadyState.OPEN

  useEffect(() => {
    if (!isConnected) {
      return
    }

    sendJsonMessage({
      type: 'subscribe',
      data: {
        channel_id: channelId,
      },
    })
  }, [channelId, isConnected, sendJsonMessage])

  useWillUnmount(() => {
    if (!isConnected) {
      return
    }

    return sendJsonMessage({
      type: 'unsubscribe',
      data: {
        channel_id: channelId,
      },
    })
  })

  useEffect(() => {
    if (lastJsonMessage?.type === 'updated') {
      const price = lastJsonMessage?.data?.update?.c || 0
      setCurrentPriceData(() => {
        const delta = price24hAgo ? ((price - price24hAgo) * 100) / price24hAgo : 0

        return {
          price,
          delta,
        }
      })
    }
  }, [lastJsonMessage, price24hAgo])

  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  const chain = chains?.find((chain) => chain.name === token.network) ?? { name: 'UNKN' }

  return (
    <>
      <div className={clsx(styles.container, className)} onClick={handleOpen}>
        <TokenAsset
          symbol={token.symbols}
          logo={token.logoURI}
          size="md"
          network={chain}
          className={styles.asset}
        />

        <span className={styles.price}>
          <Value value={formatNumber(currentPriceData.price)} prefix="$" className={styles.value} />{' '}
          <Delta value={currentPriceData.delta} className={styles.delta} />
        </span>
      </div>

      <Dialog isOpen={isOpen} onClose={handleClose} isMaximized>
        <TokensExplorerContent className={clsx(styles.dialog)} chains={chains} />
      </Dialog>
    </>
  )
}
