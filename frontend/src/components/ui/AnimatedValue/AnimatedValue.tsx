import { DetailedHTMLProps, FC, HTMLAttributes } from 'react'

import clsx from 'clsx'
import { isNumber } from 'lodash'

import Show from '@/components/ui/Show'
import { formatNumber } from '@/utils/numbers'

import styles from './AnimatedValue.module.scss'

type AnimatedValueProps = DetailedHTMLProps<HTMLAttributes<HTMLSpanElement>, HTMLSpanElement> & {
  className?: string
  value: number | string
}

export const AnimatedValue: FC<AnimatedValueProps> = ({ className, value, ...props }) => {
  const val = isNumber(value) ? formatNumber(value) : `${value}`

  return (
    <span {...props} className={clsx(styles.container, className)}>
      <span className={styles.body}>
        <span className={styles.viz} aria-hidden="true">
          {val.split('').map((char, cIdx) => {
            const isNumber = !isNaN(+char)

            return (
              <span key={cIdx} className={styles.char} data-d={isNumber ? char : undefined}>
                <Show if={!isNumber}>{char}</Show>
                <Show if={isNumber}>
                  {[...Array(10).keys()].map((digit, dIdx) => (
                    <span key={dIdx} className={clsx(styles.digit, styles[`d${digit}`])}>
                      {digit}
                    </span>
                  ))}
                </Show>
              </span>
            )
          })}
        </span>
        <span className={styles.read}>{val}</span>
      </span>
    </span>
  )
}
