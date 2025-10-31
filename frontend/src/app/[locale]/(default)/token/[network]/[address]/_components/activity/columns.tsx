import Image from 'next/image'
import Link from 'next/link'

import { ReactNode } from 'react'

import clsx from 'clsx'

import { renderFormatNumber } from '@/components/atoms/Value/utils'
import Copy from '@/components/ui/Copy'
import Meter from '@/components/ui/Meter'
import Show from '@/components/ui/Show'
import { TableColumnProps } from '@/components/ui/Table/types'
import TimerCountdown from '@/components/ui/TimerCountdown'
import IconUnknown from '@/images/emoji/hmm.svg'
import IconIn from '@/images/icons/tx-in.svg'
import IconOut from '@/images/icons/tx-out.svg'
import { ChainModel } from '@/models/chain'
import { TransactionModel } from '@/models/history'
import { TokenV3Model } from '@/models/token'
import { getShortAddress } from '@/utils/strings'
import { getTokenSymbolsString } from '@/utils/tokens'

import styles from './activity.module.scss'

const renderAddress = (address: string, url?: string) => {
  const content = (
    <span className={styles.address}>
      <span
        className={styles.addressValue}
        data-tooltip-content={address}
        data-tooltip-id="app-tooltip">
        {getShortAddress(address)}
      </span>
    </span>
  )

  return (
    <span className={styles.address}>
      <Show if={url}>
        <Link href={url ?? ''} className={styles.link} target="_blank" rel="noopener noreferrer">
          {content}
        </Link>
      </Show>
      <Show if={!url}>{content}</Show>

      <Copy text={address} />
    </span>
  )
}

const renderAmm = (data: TransactionModel, chain?: ChainModel) => {
  const amm = chain?.amms.find((amm) => amm.name === data.type)

  if (!amm?.logo_uri) {
    return (
      <IconUnknown
        className={styles.ammIcon}
        data-tooltip-content={amm?.display_name}
        data-tooltip-id="app-tooltip"
      />
    )
  }

  return (
    <Image
      className={styles.ammIcon}
      src={amm?.logo_uri}
      width={20}
      height={20}
      alt={amm.display_name}
      data-tooltip-content={amm.display_name}
      data-tooltip-id="app-tooltip"
    />
  )
}

const renderMethod = (data: TransactionModel, token: TokenV3Model) => {
  switch (data.transactionType) {
    case 'mint':
      return '+'
    case 'burn':
      return '🔥'
    case 'swap': {
      return data.fromAddress === token.address.toLowerCase() ? (
        <IconOut className={styles.type} />
      ) : (
        <IconIn className={styles.type} />
      )
    }
  }
}

const renderSymbol = (symbol: string): ReactNode => (
  <span
    className={styles.token}
    data-tooltip-content={`${symbol}`?.length > 12 ? `${symbol}` : undefined}
    data-tooltip-id={`${symbol}`?.length > 12 ? 'app-tooltip' : undefined}>{`${symbol}`}</span>
)

export const historyActivityColumns = (
  token: TokenV3Model,
  chain?: ChainModel,
  tradesTotal?: {
    min: number
    max: number
    total: number
  }
): TableColumnProps<TransactionModel>[] => {
  return [
    {
      title: 'Method',
      render: ({ data }) => {
        return (
          <span className={styles.method}>
            {renderMethod(data, token)}
            <span className={styles.amm}>
              {renderAmm(data, chain)}{' '}
              <span className={styles.capitalize}>{data.transactionType}</span>
            </span>
          </span>
        )
      },
      className: clsx(styles.cellMethod, styles.fixed),
    },
    {
      title: 'Out',
      render: ({ data, vars }) => {
        if (data.transactionType === 'burn') {
          return <div className={styles.lp}>LP</div>
        }

        return (
          <div className={styles.data}>
            {(vars?.outAmounts as number[])?.map((item, idx) => (
              <div className={styles.data} key={idx}>
                {renderFormatNumber(item)}
              </div>
            ))}
          </div>
        )
      },
      type: 'number',
      className: styles.cellAmount,
    },
    {
      render: ({ data, vars }) => {
        if (data.transactionType === 'burn') {
          return renderSymbol(getTokenSymbolsString(vars?.inTokenSymbols as string[]))
        }

        return (
          <div className={styles.data}>
            {(vars?.outTokenSymbols as string[])?.map((item, idx) => (
              <div className={styles.data} key={idx}>
                <Link
                  href={`/token/${data.network}/${(vars?.outTokenAddresses as string)[idx]}`}
                  className={styles.link}>
                  {renderSymbol(`${item}`)}
                </Link>
              </div>
            ))}
          </div>
        )
      },
      className: styles.cellToken,
    },
    {
      title: 'Out Address',
      render: ({ vars }) =>
        vars?.outAddress ? (
          renderAddress(`${vars.outAddress}`)
        ) : (
          <span className={styles.sign}>–</span>
        ),
      className: styles.cellAddress,
    },
    {
      title: 'In',
      render: ({ data, vars }) => {
        if (data.transactionType === 'mint') {
          return <div className={styles.lp}>LP</div>
        }

        return (
          <div className={styles.data}>
            {(vars?.inAmounts as number[])?.map((item, idx) => (
              <div className={styles.data} key={idx}>
                {renderFormatNumber(item)}
              </div>
            ))}
          </div>
        )
      },
      type: 'number',
      className: styles.cellAmount,
    },
    {
      render: ({ data, vars }) => {
        if (data.transactionType === 'mint') {
          return renderSymbol(getTokenSymbolsString(vars?.outTokenSymbols as string[]))
        }

        return (
          <div className={styles.data}>
            {(vars?.inTokenSymbols as string[])?.map((item, idx) => (
              <div className={styles.data} key={idx}>
                <Link
                  href={`/token/${data.network}/${(vars?.inTokenAddresses as string)[idx]}`}
                  className={styles.link}>
                  {renderSymbol(`${item}`)}
                </Link>
              </div>
            ))}
          </div>
        )
      },
      className: styles.cellToken,
    },
    {
      title: 'In Address',
      render: ({ vars }) =>
        vars?.outAddress ? (
          renderAddress(`${vars.inAddress}`)
        ) : (
          <span className={styles.sign}>–</span>
        ),
      className: styles.cellAddress,
    },
    {
      title: 'Value',
      render: ({ data }) => renderFormatNumber(data.amountStable, { prefix: '$' }),
      type: 'number',
    },
    {
      title: 'Trade Size',
      render: ({ data }) => (
        <Meter
          value={{
            title: 'Trade Size',
            value: data.amountStable,
            className: data.fromAddress === token.address ? styles.negative : styles.positive,
          }}
          max={tradesTotal?.max}
          min={tradesTotal?.min}
          prefix="$"
        />
      ),
      className: styles.cellTradeSize,
      type: 'center',
    },
    {
      title: 'TX ID',
      render: ({ data }) =>
        renderAddress(
          data.transactionAddress,
          `${chain?.block_explorer.url}/tx/${data.transactionAddress}`
        ),
      className: styles.cellAddress,
      type: 'center',
    },
    {
      title: 'Ago',
      type: 'number',
      render: ({ data }) => (
        <span className={styles.time}>
          <TimerCountdown timestamp={data.timestamp * 1000} />
        </span>
      ),
      className: styles.cellAgo,
    },
  ]
}
