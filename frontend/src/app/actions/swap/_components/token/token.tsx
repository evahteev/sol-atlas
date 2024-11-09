import Image from 'next/image'

import { FC } from 'react'

import clsx from 'clsx'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import { Caption, Show } from '@/components/ui'
import IconUnknown from '@/images/icons/question.svg'
import { TokenModel } from '@/models/token'
import { getTokenSymbolsString } from '@/utils/tokens'

import styles from './token.module.scss'

type PageActionsSwapTokenProps = {
  className?: string
  onSelect?: (token: TokenModel) => void
  token: TokenModel
}

export const PageActionsSwapToken: FC<PageActionsSwapTokenProps> = ({ className, token }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <Show if={token.logoURI}>
        <span className={styles.logo}>
          {token.logoURI.map((image, idx) => {
            if (!image) {
              return <IconUnknown className={styles.image} key={idx} />
            }

            return (
              <Image
                src={image || ''}
                alt={getTokenSymbolsString(token.symbols)}
                className={styles.image}
                width={32}
                height={32}
                key={idx}
              />
            )
          })}
        </span>
      </Show>
      <Show if={!token.logoURI}>
        <JazzIcon seed={jsNumberForAddress(token.address)} className={styles.image} />
      </Show>

      <Caption variant="body" size="md" className={styles.symbol}>
        {getTokenSymbolsString(token.symbols)}
      </Caption>
    </div>
  )
}
