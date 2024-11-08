import { ChangeEventHandler, FC, ReactNode, useEffect, useRef, useState } from 'react'

import clsx from 'clsx'

import { Button, Caption, Show } from '@/components/ui'
import Dialog from '@/components/ui/Dialog'
import { TokenModel } from '@/models/token'
import { getNumber } from '@/utils/numbers'

import { PageActionsSwapTokens } from '../tokens/tokens'

import styles from './field.module.scss'

type PageActionsSwapFieldProps = {
  className?: string
  caption: ReactNode
  token?: TokenModel
  skipToken?: TokenModel
  amount?: number
  onChangeToken?: (token: TokenModel) => void
  onChangeAmount?: (value: number) => void
}

export const PageActionsSwapField: FC<PageActionsSwapFieldProps> = ({
  className,
  caption,
  token,
  skipToken,
  amount = 0,
  onChangeToken,
  onChangeAmount,
}) => {
  const [currentValue, setCurrentValue] = useState(`${amount}`)

  useEffect(() => {
    if (amount === getNumber(currentValue)) {
      return
    }

    onChangeAmount?.(getNumber(currentValue))
  }, [amount, currentValue, onChangeAmount])

  const [isOpen, setIsOpen] = useState(false)
  const refInput = useRef<HTMLInputElement>(null)

  const handleBlur = () => {
    if (!currentValue) {
      setCurrentValue('0')
    }
  }

  const handleFocus = () => {
    refInput?.current?.select()
  }

  const handleChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const newVal = e.target.value

    if (!newVal) {
      setCurrentValue('')
      return
    }

    const match = `0${newVal}`.match(/^\d{1,}(\.\d{0,})?$/)

    if (!match) {
      return
    }

    const clearedVal = newVal.replace(/^0+/, '0')
    const numberVal = parseFloat(newVal)
    setCurrentValue(`${isNaN(numberVal) ? '0' : ''}${clearedVal}`)
  }

  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  const handleSelect = (token: TokenModel) => {
    onChangeToken?.(token)
    setIsOpen(false)
    onChangeToken?.(token)
  }

  return (
    <>
      <div className={clsx(styles.container, className)}>
        <label className={styles.field}>
          <Caption className={styles.title} variant="body" size="sm">
            {caption}
          </Caption>
          <input
            ref={refInput}
            className={styles.amount}
            type="text"
            min={0}
            value={currentValue}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
          />
        </label>

        <Button variant="primary" size="lg" className={styles.toggle} onClick={handleOpen}>
          <Show if={token}>{token?.symbols}</Show>
          <Show if={!token}>Choose token</Show>
        </Button>
      </div>

      <Dialog isOpen={isOpen} onClose={handleClose}>
        <Show if={isOpen}>
          <PageActionsSwapTokens
            onChange={handleSelect}
            caption={`Select Token to ${caption}`}
            skipToken={skipToken}
          />
        </Show>
      </Dialog>
    </>
  )
}
