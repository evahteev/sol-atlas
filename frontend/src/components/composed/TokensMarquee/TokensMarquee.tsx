import { FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import { Marquee } from '@/components/ui/Marquee/Marquee'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import { TokensMarqueeSwap } from './TokensMarqueeSwap'

import styles from './TokensMarquee.module.scss'

type TokensMarqueeProps = HTMLAttributes<HTMLDivElement> & {
  title?: ReactNode
  tokens: Pick<TokenV3Model, 'address' | 'network' | 'logoURI' | 'symbols' | 'priceUSDChange24h'>[]
  chains: ChainModel[]
  className?: string
}

export const TokensMarquee: FC<TokensMarqueeProps> = ({
  title,
  tokens,
  chains,
  className,
  ...rest
}: TokensMarqueeProps) => {
  return (
    <Marquee
      items={tokens.map((token, idx) => {
        const children = (
          <>
            <span className={styles.index}>#{idx + 1}</span>
            <TokensMarqueeSwap
              token={token}
              network={
                chains.find((chain) => chain.name === token?.network) ?? {
                  name: 'UNKN',
                  color: 'grey',
                }
              }
            />
          </>
        )

        return {
          children,
        }
      })}
      title={title}
      className={clsx(styles.container, className)}
      {...rest}
    />
  )
}
