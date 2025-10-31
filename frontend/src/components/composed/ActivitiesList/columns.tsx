import Link from 'next/link'

import { ReactNode } from 'react'

import clsx from 'clsx'

import { renderFormatNumber } from '@/components/atoms/Value/utils'
import Copy from '@/components/ui/Copy'
import Show from '@/components/ui/Show'
import { TableColumnProps } from '@/components/ui/Table/types'
import TimerCountdown from '@/components/ui/TimerCountdown'
import IconSwap from '@/images/icons/swap.svg'
import IconIn from '@/images/icons/tx-in.svg'
import IconOut from '@/images/icons/tx-out.svg'
import { TransactionModel } from '@/models/history'
import { getShortAddress } from '@/utils/strings'

import { RowVarsProps } from './helpers'

import styles from './ActivitiesList.module.scss'

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
    <>
      <Show if={url}>
        <Link href={url ?? ''} className={styles.link} target="_blank" rel="noopener noreferrer">
          {content}
        </Link>
      </Show>

      <Show if={!url}>{content}</Show>
    </>
  )
}

const renderSymbol = (symbol: string): ReactNode => (
  <span
    className={styles.token}
    data-tooltip-content={`${symbol}`?.length > 12 ? `${symbol}` : undefined}
    data-tooltip-id={`${symbol}`?.length > 12 ? 'app-tooltip' : undefined}>
    {symbol || <>&nbsp;</>}
  </span>
)

const renderType = (value: string) => {
  const val = value?.toLocaleLowerCase()

  if (['erc20', 'erc721', 'native_transfer'].includes(val)) {
    return 'Transfer'
  }

  if (val === 'swap') {
    return 'Swap'
  }

  return value
}

export const accountActivityColumns = (
  address: string
): TableColumnProps<Partial<TransactionModel>, RowVarsProps>[] => {
  return [
    {
      title: 'Method',
      render: ({ data }) => {
        const type = data?.transactionType?.toLocaleLowerCase()
        const walletIndex =
          data?.wallets?.findIndex(
            (wallet) => wallet.toLocaleLowerCase() === address.toLocaleLowerCase()
          ) ?? 0

        return (
          <span className={styles.method}>
            <Show if={type === 'swap'}>
              <IconSwap className={styles.type} />
            </Show>

            <Show if={type !== 'swap'}>
              <Show if={walletIndex === 0}>
                <Show if={(data?.amounts?.[walletIndex] ?? 0) >= 0}>
                  <IconOut className={styles.type} />
                </Show>

                <Show if={(data?.amounts?.[walletIndex] ?? 0) < 0}>
                  <IconIn className={styles.type} />
                </Show>
              </Show>

              <Show if={walletIndex === 1}>
                <Show if={(data?.amounts?.[walletIndex] ?? 0) < 0}>
                  <IconOut className={styles.type} />
                </Show>

                <Show if={(data?.amounts?.[walletIndex] ?? 0) >= 0}>
                  <IconIn className={styles.type} />
                </Show>
              </Show>
            </Show>

            <span className={styles.amm}>
              <span className={styles.capitalize}>{renderType(`${data.transactionType}`)}</span>
            </span>
          </span>
        )
      },
      className: clsx(styles.cellMethod, styles.fixed),
    },

    {
      title: 'Out',
      render: ({ data, vars }) => {
        const wallet = data?.wallets?.[0]

        return (
          <div className={styles.data}>
            <div className={styles.main}>
              {renderFormatNumber(Math.abs(data?.amounts?.[0] ?? 0))}
            </div>

            <Show if={wallet}>
              <div className={styles.aside}>
                {renderAddress(`${wallet}`, `${vars?.chain?.block_explorer.url}/address/${wallet}`)}
              </div>
            </Show>
          </div>
        )
      },
      type: 'number',
      className: styles.cellAmount,
    },
    {
      render: ({ data }) => {
        return (
          <div className={styles.data}>
            <div className={styles.main}>
              <Link
                href={`/token/${data.network}/${data?.tokenAddresses?.[0]}`}
                className={styles.link}>
                {renderSymbol(
                  data.transactionType === 'erc721' ? 'NFT' : `${data?.symbols?.[0] || ''}`
                )}
              </Link>
            </div>

            <Show if={data?.wallets?.[0]}>
              <div className={styles.aside}>
                <Copy text={data?.wallets?.[0] || ''} size="xxs" className={styles.copy} />
              </div>
            </Show>
          </div>
        )
      },
      className: styles.cellToken,
    },

    {
      title: 'In',
      render: ({ data, vars }) => {
        const amount = data?.amounts?.[1] ?? data?.amounts?.[0]
        const wallet = data?.wallets?.[1] || data?.wallets?.[0]

        return (
          <div className={styles.data}>
            <div className={styles.main}>{renderFormatNumber(Math.abs(amount ?? 0))}</div>

            <Show if={wallet}>
              <div className={styles.aside}>
                {renderAddress(`${wallet}`, `${vars?.chain?.block_explorer.url}/address/${wallet}`)}
              </div>
            </Show>
          </div>
        )
      },
      type: 'number',
      className: styles.cellAmount,
    },
    {
      render: ({ data }) => {
        return (
          <div className={styles.data}>
            <div className={styles.main}>
              <Link
                href={`/token/${data.network}/${data?.tokenAddresses?.[1] || data?.tokenAddresses?.[0]}`}
                className={styles.link}>
                {renderSymbol(
                  data.transactionType === 'erc721'
                    ? 'NFT'
                    : `${data?.symbols?.[1] || data?.symbols?.[0] || ''}`
                )}
              </Link>
            </div>

            <Show if={data?.wallets?.[0]}>
              <div className={styles.aside}>
                <Copy
                  text={data?.wallets?.[1] || data?.wallets?.[0] || ''}
                  size="xxs"
                  className={styles.copy}
                />
              </div>
            </Show>
          </div>
        )
      },
      className: styles.cellToken,
    },

    {
      title: 'Value',
      render: ({ data }) => renderFormatNumber(data.amountStable, { prefix: '$' }),
      type: 'number',
    },

    {
      title: 'TX ID',
      render: ({ data, vars }) => {
        return renderAddress(
          `${data.transactionAddress}`,
          `${vars?.chain?.block_explorer.url}/tx/${data.transactionAddress}`
        )
      },
      className: styles.cellAddress,
      type: 'center',
    },
    {
      title: 'Ago',
      type: 'number',
      render: ({ data }) => (
        <span className={styles.time}>
          <TimerCountdown timestamp={(data.timestamp || 0) * 1000} isCompact suffix="ago" />
        </span>
      ),
      className: styles.cellAgo,
    },
  ]
}
