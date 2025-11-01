import { ChangeEventHandler, FC, useState } from 'react'

import clsx from 'clsx'

import Caption from '@/components/ui/Caption'
import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import TooltipAnchor from '@/components/ui/TooltipAnchor'
import { inputNumberParseValue } from '@/utils/numbers'

import styles from './slippage.module.scss'

export const TaskFormCustomSwapTokenSlippage: FC<{
  options?: number[]
  className?: string
  value?: number
  onValueChange?: (value: number) => void
}> = ({ className, options, value, onValueChange }) => {
  const [currentValue, setCurrentValue] = useState<number>(value || 0.5)
  const [customValue, setCustomValue] = useState('')

  const handleChangeValue: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { number, value } = inputNumberParseValue(e.target.value)
    setCustomValue(value)
    setCurrentValue(number)
    onValueChange?.(number)
  }

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <Caption size="sm" className={styles.caption}>
          Max Slippage
        </Caption>{' '}
        <TooltipAnchor text="Your transaction will fail if the price changes more than the slippage." />
      </div>
      <div className={styles.body}>
        <ul className={styles.list}>
          {options?.map((option, idx) => (
            <li className={styles.item} key={idx}>
              <button
                className={clsx(styles.option, {
                  [styles.active]: value === option && !customValue,
                })}
                onClick={() => {
                  onValueChange?.(option)
                  setCustomValue('')
                }}>
                {option}%
              </button>
            </li>
          ))}
          <li className={styles.item}>
            <input
              placeholder="Custom"
              value={customValue ? `${customValue}%` : ''}
              name="slippage"
              min={0.1}
              max={1}
              step={0.1}
              inputMode="numeric"
              className={clsx(styles.option, { [styles.active]: !!customValue })}
              onChange={handleChangeValue}
            />
          </li>
        </ul>
      </div>

      <Show if={currentValue >= 1}>
        <div className={styles.footer}>
          <Message type="warn" className={styles.message}>
            You may receive up to {currentValue}% less tokens
          </Message>
        </div>
      </Show>
    </div>
  )
}
