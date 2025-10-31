'use client'

import Image from 'next/image'

import { HTMLAttributes, createElement } from 'react'

import clsx from 'clsx'

import Delta from '@/components/atoms/Delta'
import ImageFallback from '@/components/atoms/ImageFallback'
import Value from '@/components/atoms/Value'
import Show from '@/components/ui/Show'
import IconUnknown from '@/images/emoji/hmm.svg'
import IconUnverified from '@/images/emoji/nospeak.svg'
import IconVerified from '@/images/emoji/verified.svg'
import { AmmModel } from '@/models/amm'
import { getAsArray, removeUnprintable } from '@/utils'
import { formatNumber } from '@/utils/numbers'
import { getTokenSymbolsString } from '@/utils/tokens'

import styles from './TokenAsset.module.scss'

type TokenAssetProps = HTMLAttributes<HTMLDivElement> & {
  className?: string
  symbol: string | string[]
  logo: string | string[]
  network?: { name: string; color?: string }
  color?: string
  href?: string
  onlyAvatar?: boolean
  hideNetwork?: boolean
  isLP?: boolean
  amm?: string
  description?: string
  size?: 'md' | 'lg' | 'sm'
  verified?: boolean
  price?: number
  delta?: number
}

export function TokenAsset({
  className,
  symbol,
  logo,
  network,
  href,
  color,
  onlyAvatar,
  hideNetwork,
  isLP,
  amm,
  description,
  size = 'lg',
  verified,
  price,
  delta,
}: TokenAssetProps) {
  const networkObj: { color?: string; name: string; amms?: AmmModel[] } = network ?? {
    name: 'UNKNOWN',
  }

  const logoArr = getAsArray(logo)
  const symbolArr = getAsArray(symbol)

  const ammObj = networkObj.amms?.find((item) => item.name === amm)

  const networkName = networkObj.name.toUpperCase()

  const NoImage = verified ? IconUnknown : IconUnverified

  const content = (
    <>
      <span className={styles.avatar}>
        <Show if={!logo}>
          <span className={styles.icon}>
            <NoImage className={styles.image} />
          </span>
        </Show>

        {logoArr?.map((logoItem, idx) => (
          <span key={idx} className={styles.icon}>
            <Show if={logoItem}>
              <ImageFallback
                className={styles.image}
                src={logoItem}
                alt={removeUnprintable(symbolArr?.[idx]) ?? ''}
                width={32}
                height={32}
                fallback={<NoImage className={styles.image} />}
              />
            </Show>

            <Show if={!logoItem}>
              <NoImage className={styles.image} />
            </Show>
          </span>
        ))}
      </span>

      <Show if={!onlyAvatar}>
        <span className={styles.body}>
          <span className={styles.caption}>
            <span className={styles.symbol}>{getTokenSymbolsString(symbolArr)}</span>{' '}
            <Show if={isLP && !!ammObj?.logo_uri}>
              <Image
                src={ammObj?.logo_uri || ''}
                className={styles.amm}
                width={32}
                height={32}
                alt={ammObj?.name || ''}
              />
            </Show>
            <Show if={isLP}>
              <span className={styles.lp}>LP</span>{' '}
            </Show>
            <Show if={!hideNetwork && !!network}>
              <span className={styles.network}>
                {networkName.substring(
                  0,
                  networkName === 'SOLANA' ? 6 : Math.min(4, networkObj.name.length)
                )}
              </span>
            </Show>{' '}
            <Show if={verified}>
              <IconVerified className={styles.verified} />
            </Show>
          </span>

          <Show if={isFinite(Number(price))}>
            <span className={styles.price}>
              <Delta value={delta || 0} className={styles.delta} />
              <Value value={formatNumber(price || 0)} prefix="$" className={styles.value} />
            </span>
          </Show>
        </span>
      </Show>
    </>
  )

  return createElement(
    href ? 'a' : 'span',
    {
      'data-tooltip-content': description,
      'data-tooltip-id': description ? 'app-tooltip' : undefined,
      className: clsx(styles.container, styles[size], className),
      href,
      style: { '--network-color': networkObj.color || color },
    },
    content
  )
}
