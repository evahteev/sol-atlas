'use client'

import { FC, useState } from 'react'

import clsx from 'clsx'

import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { TokenV3Model, TokenV3ModelWithBalances } from '@/models/token'

import TokenBalanceSelector from '../../../TokenBalanceSelector'
import TokenSelector from '../../../TokenSelector'

import styles from './TaskFormFieldToken.module.scss'

type TaskFormTokenProps = {
  className?: string
  name: string
  caption?: string | null
  account?: string
  tokenId?: string
  tokenList?: TokenV3Model[]
}

export const TaskFormFieldToken: FC<TaskFormTokenProps> = ({
  className,
  name,
  caption,
  account,
  tokenList,
}) => {
  const [currentToken, setCurrentToken] = useState<
    TokenV3Model | TokenV3ModelWithBalances | undefined
  >(tokenList?.[0])

  const onSelectChange = (token?: TokenV3Model | TokenV3ModelWithBalances) => {
    setCurrentToken(token)
  }

  const setAmount = (percent: number) => {
    // TODO: THIS IS NOT A RIGHT WAY TO DO THIS!
    // TODO: THIS IS MADE AS EXTREMELY TEMPORARILY SOLUTION!
    // TODO: FIX ASAP! FIX ASAP! FIX ASAP! FIX ASAP! FIX ASAP!
    const el = document.getElementById('form_sell_amount') as HTMLInputElement | null

    if (!el) {
      return
    }

    el.value = `${(((currentToken as TokenV3ModelWithBalances)?.balance ?? 0) * percent) / 100}`
  }

  const isForBalance = ['token_sell', 'token_send'].includes(name)

  return (
    <>
      <FormField
        className={clsx(styles.container, className)}
        type="display"
        caption={
          <div className={styles.header}>
            <span className={styles.fieldCaption}>{caption}</span>

            <Show if={isForBalance}>
              <div className={styles.tools}>
                {[25, 50, 75].map((percent, idx) => (
                  <Button
                    isDisabled={!currentToken}
                    key={`${idx}-${percent}`}
                    caption={`${percent}%`}
                    isOutline
                    size="xxs"
                    className={styles.tool}
                    onClick={() => setAmount(percent)}
                  />
                ))}

                <Button
                  isDisabled={!currentToken}
                  caption="MAX"
                  isOutline
                  size="xxs"
                  className={styles.tool}
                  onClick={() => setAmount(100)}
                />
              </div>
            </Show>
          </div>
        }>
        <Show if={isForBalance}>
          <TokenBalanceSelector
            onTokenChange={onSelectChange}
            className={styles.selector}
            account={account}
          />
        </Show>

        <Show if={!isForBalance}>
          <TokenSelector
            includeNative
            onTokenChange={onSelectChange}
            className={styles.selector}
            account={account}
            tokenList={tokenList}
            token={currentToken}
          />
        </Show>

        <input
          value={currentToken ? `${currentToken.address}-${currentToken.network}` : ''}
          name={name}
          type="hidden"
        />
      </FormField>
    </>
  )
}
