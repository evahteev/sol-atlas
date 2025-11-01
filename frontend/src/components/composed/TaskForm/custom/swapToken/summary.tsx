import { FC, useContext } from 'react'

import clsx from 'clsx'

import Properties from '@/components/atoms/Properties'
import Value from '@/components/atoms/Value'
import Card from '@/components/ui/Card'
import { AppContext } from '@/providers/context'
import { formatNumber } from '@/utils/numbers'
import { getTokenSymbolsString } from '@/utils/tokens'

import { SwapSummary } from './types'

import styles from './summary.module.scss'

type TaskFormCustomSwapTokenSummaryProps = SwapSummary & { className?: string; reward?: number }

export const TaskFormCustomSwapTokenSummary: FC<TaskFormCustomSwapTokenSummaryProps> = ({
  className,
  reward,
  tokenFrom,
  tokenTo,
}) => {
  const {
    config: { pointsToken },
  } = useContext(AppContext)

  const priceRatio = formatNumber((tokenFrom?.priceUSD || 0) / (tokenTo.priceUSD || 1))

  return (
    <Card className={clsx(styles.container, className)}>
      <Properties
        align="end"
        className={styles.properties}
        items={[
          {
            caption: 'Rate',
            value: (
              <span className={styles.rate}>
                1 {getTokenSymbolsString(tokenFrom.symbols)} ≈ {priceRatio}{' '}
                {getTokenSymbolsString(tokenTo.symbols)}
              </span>
            ),
          },
          {
            caption: 'Network Fee',
          },
          {
            caption: 'Guru Network Fee (1%)',
          },
          {
            caption: 'Reward Amount',
            value: (
              <Value
                value={`+${reward}`}
                suffix={` ${pointsToken.symbols[0]}`}
                className={styles.reward}
              />
            ),
          },
        ]}
      />
    </Card>
  )
}
