'use client'

import { FC, useEffect, useRef } from 'react'

import clsx from 'clsx'
import { Overlay } from 'klinecharts'
import omit from 'lodash/omit'
import { env } from 'next-runtime-env'
import useWebSocket from 'react-use-websocket'
import { useDidMount, useLocalstorageState, useWillUnmount } from 'rooks'

import { KLineChartPro, Period } from '@/lib/dash-guru'
import { TokenHistoryCandle } from '@/models/candle'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { convertTimespan } from '@/utils/dates'
import { getFirstSignificantDecimalIndex, getIntegerPart } from '@/utils/numbers'
import { getShortAddress } from '@/utils/strings'
import { getTokenPriceChannel, getTokenSymbolsString } from '@/utils/tokens'

import { FinancialChartDatafeed } from './Datafeed'

import styles from './FinancialChart.module.scss'

type FinancialChartProps = {
  className?: string
  token: TokenV3Model
  chains: ChainModel[]
}

const CHART_KEY = 'gurunetwork_token_chart'

export const FinancialChart: FC<FinancialChartProps> = ({ className, token, chains }) => {
  const ref = useRef(null)
  const refWM = useRef(null)
  const refCallback = useRef<(data: TokenHistoryCandle) => void>(null)

  const chart = useRef<KLineChartPro>(undefined)

  const [storage, setStorage] = useLocalstorageState<{
    prd?: Period
    tz?: string
    opts?: unknown
  }>(CHART_KEY, {})

  const periods = [
    { multiplier: 5, timespan: 'minute', text: '5m' },
    { multiplier: 10, timespan: 'minute', text: '10m' },
    { multiplier: 30, timespan: 'minute', text: '30m' },
    { multiplier: 1, timespan: 'hour', text: '1H' },
    { multiplier: 4, timespan: 'hour', text: '4H' },
    { multiplier: 1, timespan: 'day', text: '1D' },
  ]

  const channelId = getTokenPriceChannel(token.id, 60, chains)

  const { lastJsonMessage, sendJsonMessage } = useWebSocket<{
    type: string
    data: { update: TokenHistoryCandle; channel_id: string }
  }>(`${env('NEXT_PUBLIC_CHANNELS_WS_API')}`, {
    shouldReconnect: () => true,
    share: true,
    filter: (message) => {
      const data = JSON.parse(message.data)

      return data.type === 'updated' && data.data.channel_id === channelId
    },
  })

  const [tokenStorage, setTokenStorage] = useLocalstorageState<{
    inm?: string[]
    ins?: string[]
    ovl?: Record<string, Overlay>
  }>(`${CHART_KEY}-${token.id}`, {})

  useEffect(() => {
    if (lastJsonMessage?.data?.update) {
      refCallback.current?.(lastJsonMessage?.data?.update)
    }
  }, [lastJsonMessage])

  const unsubscribe = () => {
    if (!channelId) {
      return
    }
    sendJsonMessage({
      type: 'unsubscribe',
      data: {
        channel_id: channelId,
      },
    })
  }

  useWillUnmount(() => {
    return unsubscribe
  })

  useDidMount(() => {
    if (!ref?.current || chart?.current) {
      return
    }

    const currentPeriod =
      periods.find(
        (period) =>
          period.multiplier === storage?.prd?.multiplier &&
          period.timespan === storage?.prd?.timespan
      ) || periods[3]

    chart.current = new KLineChartPro({
      container: ref.current,
      watermark:
        refWM?.current ||
        `${getTokenSymbolsString(token.symbols)} ${token.network.toUpperCase().substring(0, 4)}`,

      // Default symbol info
      symbol: {
        exchange: token.AMM,
        market: 'crypto',
        name: token.name,
        shortName: getTokenSymbolsString(token.symbols),
        ticker: `${token.address.toLowerCase()}-${token.network.toLowerCase()}_USD`,
        priceCurrency: 'USD',
        type: 'ADRC',
        pricePrecision: Math.max(7, getFirstSignificantDecimalIndex(token.priceUSD) + 1),
      },
      periods,
      datafeed: new FinancialChartDatafeed({
        onSubscribe: (period, callback) => {
          sendJsonMessage({
            type: 'subscribe',
            data: {
              channel_id: channelId,
            },
          })

          refCallback.current = (data) => {
            const timespan = convertTimespan(period.multiplier, period.timespan, 'second')
            const timestamp = getIntegerPart(data.t / timespan) * timespan * 1000
            callback({
              timestamp,
              open: data.o,
              high: data.h,
              low: data.l,
              close: data.c,
              volume: data.v,
              turnover: data.vw,
            })
          }
        },
        onUnsubscribe: unsubscribe,
      }),
      theme: 'dark',
      locale: 'en-US',
      drawingBarVisible: false,

      // Default period
      period: currentPeriod,
      timezone: storage?.tz || 'UTC',
      mainIndicators: tokenStorage?.inm || ['MA'],
      subIndicators: tokenStorage?.ins || ['VOL'],
      styles: storage?.opts || undefined,
      overlays: Object.values(tokenStorage?.ovl || {}),

      onMainIndicatorsChange: (val: string[]) => {
        setTokenStorage({ ...tokenStorage, inm: val })
      },

      // @ts-expect-error TODO: fix typings
      onSubIndicatorsChange: (val: Record<string, unknown>) => {
        setTokenStorage({ ...tokenStorage, ins: Object.keys(val) })
      },
      onSettingsChange: (val: unknown) => {
        setStorage({ ...storage, opts: val })
      },
      onTimezoneChange: (val: string) => {
        setStorage({ ...storage, tz: val })
      },
      onPeriodChange: (val: Period) => {
        setStorage({ ...storage, prd: val })
      },
      onOverlayChange: (overlay: Overlay) => {
        const overlayData = Object.fromEntries(
          Object.entries(overlay).filter(([, value]) =>
            ['string', 'number', 'boolean', 'object'].includes(typeof value)
          )
        ) as Overlay
        const newState = {
          ...tokenStorage,
          ovl: { ...tokenStorage.ovl, [overlay.id]: overlayData },
        }
        setTokenStorage(newState)
      },
      onOverlayRemove: (overlay: Overlay) => {
        setTokenStorage(omit(tokenStorage, `ovl.${overlay.id}`))
      },
    })
  })

  return (
    <div className={clsx(styles.container, className)} ref={ref}>
      <strong className={styles.watermark} ref={refWM}>
        <span className={styles.watermarkSymbol}>{getTokenSymbolsString(token.symbols)}</span>{' '}
        <span className={styles.watermarkNetwork}>
          ({token.network.toUpperCase().substring(0, 4)})
        </span>
        <span className={styles.watermarkAddress}>{getShortAddress(token.address)}</span>
      </strong>
    </div>
  )
}
