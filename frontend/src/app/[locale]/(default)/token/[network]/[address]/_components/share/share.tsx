'use client'

import { FC, useCallback } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'
import IconShare from '@/images/icons/share.svg'
import { TokenV3Model } from '@/models/token'
import { formatNumber } from '@/utils/numbers'
import { getTokenSymbolsString } from '@/utils/tokens'

import styles from './share.module.scss'

type PageTokenShareButtonProps = ButtonProps & {
  token: TokenV3Model
}
export const PageTokenShareButton: FC<PageTokenShareButtonProps> = ({ token, ...props }) => {
  const onShareTelegramHandler = useCallback(() => {
    const text = `
💰 **${token.name}** (${getTokenSymbolsString(token.symbols)})
💵 **Price:** $${formatNumber(token.priceUSD, { precisionMode: true })} (24h Change: ${formatNumber(token.priceUSDChange24h * 100)}%)
💧 **Liquidity:** $${formatNumber(token.liquidityUSD)}
📊 **24h Volume:** $${formatNumber(token.volume24hUSD)}`
    const url = `${window.location.origin}/token/${token.network}/${token.address}`

    navigator
      .share({
        title: `${token.name} (${getTokenSymbolsString(token.symbols)})`,
        text,
        url,
      })
      .catch((e) => console.error(e))
  }, [
    token.address,
    token.liquidityUSD,
    token.name,
    token.network,
    token.priceUSD,
    token.priceUSDChange24h,
    token.symbols,
    token.volume24hUSD,
  ])

  return (
    <Button
      {...props}
      className={clsx(styles.action, props.className)}
      onClick={onShareTelegramHandler}
      icon={<IconShare className={styles.icon} />}
    />
  )
}

export default PageTokenShareButton
