'use client'

import { ChangeEventHandler, FC, FocusEventHandler, useContext, useEffect, useState } from 'react'

import { useAppKitAccount } from '@reown/appkit/react'
import clsx from 'clsx'
import { useSession } from 'next-auth/react'

import Loader from '@/components/atoms/Loader'
import Value from '@/components/atoms/Value'
import ChainSelector from '@/components/composed/ChainSelector'
import Display from '@/components/composed/Display'
import FormField from '@/components/composed/FormField'
import { TaskFormProps } from '@/components/composed/TaskForm/types'
import TokenSelector from '@/components/composed/TokenSelector'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Show from '@/components/ui/Show'
import { useTokens } from '@/hooks/tokens/useTokens'
import { WalletType, useWalletAddress } from '@/hooks/useWalletAddress'
import { useWalletTotals } from '@/hooks/useWalletTotals'
import IconChange from '@/images/icons/change.svg'
import IconRefetch from '@/images/icons/reload.svg'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { AppContext } from '@/providers/context'
import { formatNumber, inputNumberParseValue } from '@/utils/numbers'

import { TaskFormCustomSwapTokenSlippage } from './slippage'
import { TaskFormCustomSwapTokenSummary } from './summary'
import { SwapSummary } from './types'

import styles from './swapToken.module.scss'

const TaskFormCustomSwapToken: FC<TaskFormProps> = ({ variables = {}, isLoading, onComplete }) => {
  const { data: session } = useSession()
  const { chains } = useContext(AppContext)
  const thirdWebWallet = useWalletAddress(WalletType.thirdweb_ecosystem)
  const { address } = useAppKitAccount()
  const wallet = Object.keys(variables).some((x) => x.includes('externalWallet_'))
    ? address
    : thirdWebWallet

  const { data: initTokens } = useTokens({
    ids: [`${variables.token_buy?.value || ''}`, `${variables.token_sell?.value || ''}`],
  })

  const [variablesValues, setVariablesValues] = useState<{
    action_swap: boolean | null
    chain_id: number | null
    dst_chain_id: number | null
    form_autoconfirm_swap: boolean | null
    form_max_slippage_percentage: number | null
    form_sell_amount: string | null
    token_buy: string | null
    token_sell: string | null
    externalWallet_walletAddress?: string | null
  }>({
    action_swap: variables.action_swap?.value === 'true',
    chain_id: Number(variables.chain_id?.value) || chains[0].id || null,
    dst_chain_id: Number(variables.dst_chain_id?.value) || chains[0].id || null,
    form_autoconfirm_swap: variables.form_autoconfirm_swap?.value === 'true',
    form_max_slippage_percentage: Number(variables.form_max_slippage_percentage?.value),
    form_sell_amount: `${variables.form_sell_amount?.value || 0}`,
    token_sell: `${variables.token_sell?.value || ''}` || null,
    token_buy: `${variables.token_buy?.value || ''}` || null,
    externalWallet_walletAddress: `${variables.externalWallet_walletAddress?.value || ''}` || null,
  })

  const initialChainFrom =
    chains.find((chain) => chain.id === variablesValues.chain_id) ?? chains[0]
  const initialChainTo =
    chains.find((chain) => chain.id === variablesValues.dst_chain_id) ?? chains[0]

  const { tokens, natives, isFetching, refetch } = useWalletTotals({
    address: `${wallet ?? ''}`,
    chains,
    refetchInterval: 30 * 1000,
    initialData: {
      // tokens: variables.warehouse_query_result?.value ?? [],
    },
  })

  const tokensBalance = [...tokens, ...natives]

  const [values, setValues] = useState<
    SwapSummary & {
      isShowSettings: boolean
      slippage: number
      amountValue: string
    }
  >({
    chainFrom: initialChainFrom,
    chainTo: initialChainTo,
    tokenFrom: initTokens?.find((token) => token.id === `${variables.token_sell?.value || ''}`) || {
      ...initialChainFrom.native_token,
      network: initialChainFrom.name,
    },
    tokenTo: initTokens?.find((token) => token.id === `${variables.token_buy?.value || ''}`) || {
      ...initialChainTo.native_token,
      network: initialChainFrom.name,
    },
    amount: Number(variablesValues.form_sell_amount || 0),
    slippage: variablesValues.form_max_slippage_percentage || 0.5,
    isShowSettings: false,
    amountValue: `${variablesValues.form_sell_amount || ''}`,
  })

  useEffect(() => {
    setVariablesValues((prev) => ({
      ...prev,
      chain_id: values.chainFrom.id,
      dst_chain_id: values.chainTo.id,
      token_sell: values.tokenFrom.id,
      token_buy: values.tokenTo.id,
      form_sell_amount: `${values.amount}`,
      form_max_slippage_percentage: values.slippage,
    }))
  }, [values])

  useEffect(() => {
    if (initTokens?.length) {
      setValues((prev) => ({
        ...prev,
        tokenFrom: initTokens?.find(
          (token) => token.id === `${variables.token_sell?.value || ''}`
        ) || {
          ...prev.tokenFrom,
        },
        tokenTo: initTokens?.find(
          (token) => token.id === `${variables.token_buy?.value || ''}`
        ) || {
          ...prev.tokenTo,
        },
      }))
    }
  }, [initTokens, variables.token_buy?.value, variables.token_sell?.value])

  useEffect(() => {
    if (Object.keys(variables).some((x) => x.includes('externalWallet_')) && address) {
      setVariablesValues((prev) => ({
        ...prev,
        externalWallet_walletAddress: address,
      }))
    }
  }, [address, variables])

  if (isLoading) {
    return <Loader className={styles.loader}>Preparing swaps...</Loader>
  }

  const amountTo =
    (values.amount * (values.tokenFrom?.priceUSD || 0)) / (values.tokenTo.priceUSD || 1)

  const handleChangeChains = () => {
    setValues((prev) => ({
      ...prev,
      chainFrom: prev.chainTo,
      chainTo: prev.chainFrom,
      tokenFrom: prev.tokenTo,
      tokenTo: prev.tokenFrom,
      amount: amountTo,
      amountValue: inputNumberParseValue(amountTo).value,
    }))
  }

  const handleChangeChainFromValue = (chainFrom?: ChainModel) => {
    if (!chainFrom || chainFrom.id === values.chainFrom.id) {
      return
    }

    setValues((prev) => ({
      ...prev,
      chainFrom,
      tokenFrom: { ...chainFrom.native_token, verified: true, network: chainFrom.name },
    }))
  }

  const handleChangeChainToValue = (chainTo?: ChainModel) => {
    if (!chainTo || chainTo.id === values.chainTo.id) {
      return
    }

    setValues((prev) => ({
      ...prev,
      chainTo,
      tokenTo: { ...chainTo.native_token, verified: true, network: chainTo.name },
    }))
  }

  const handleChangeTokenFromValue = (tokenFrom?: TokenV3Model) => {
    setValues((prev) => ({
      ...prev,
      tokenFrom: tokenFrom ?? {
        ...prev.chainFrom.native_token,
        verified: true,
        network: prev.chainFrom.name,
      },
    }))
  }

  const handleChangeTokenToValue = (tokenTo?: TokenV3Model) => {
    setValues((prev) => ({
      ...prev,
      tokenTo: tokenTo ?? {
        ...prev.chainTo.native_token,
        verified: true,
        network: prev.chainTo.name,
      },
    }))
  }

  const handleChangeIsShowSettings = (isShowSettings: boolean) => {
    setValues((prev) => ({ ...prev, isShowSettings }))
  }

  const handleChangeAmountValue: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { number: amount, value: amountValue } = inputNumberParseValue(e.target.value)
    setValues((prev) => ({ ...prev, amount, amountValue }))
  }

  const handleChangeSlippageValue = (slippage: number) => {
    setValues((prev) => ({ ...prev, slippage }))
  }

  const balanceFrom =
    tokensBalance.find((balance) => balance.id === values.tokenFrom.id)?.balance ?? 0
  const balanceTo = tokensBalance.find((balance) => balance.id === values.tokenTo.id)?.balance ?? 0

  const handleChangeAmountPercent = (ratio: number) => () => {
    const { number, value } = inputNumberParseValue(balanceFrom * ratio)
    setValues((prev) => ({
      ...prev,
      amount: number,
      amountValue: value,
    }))
  }

  const handleFocus: FocusEventHandler<HTMLInputElement> = (e) => {
    e.target.select()
  }

  const isInsufficientBalance = !balanceFrom || balanceFrom < values.amount
  const isAllowSwap = !isInsufficientBalance && !!values.amount

  const handleConfirm = () => {
    if (!isAllowSwap) {
      console.error('Swap is not allowed')
      return
    }

    const resultVars = Object.fromEntries(
      Object.entries(variablesValues).map(([name, value]) => {
        return [name, { value }]
      })
    )

    onComplete?.({
      business_key: `${session?.user?.id}-${values.tokenTo.id}`,
      variables: resultVars,
    })
  }

  const handleRefetch = () => {
    refetch()
  }

  const renderBalance = (balance: number) => {
    return (
      <span className={styles.balance}>
        <span className={styles.balancePrefix}>Balance: </span>
        <span className={styles.balanceAmount}>{balance}</span>{' '}
        <Button
          size="xxs"
          variant="custom"
          isOutline
          isPending={isFetching}
          icon={
            <IconRefetch className={clsx(styles.balanceIcon, { [styles.loading]: isFetching })} />
          }
          className={styles.balanceRefetch}
          onClick={handleRefetch}
        />
      </span>
    )
  }

  const buttonCaption =
    values.amount && isInsufficientBalance ? 'Insufficient balance? Top Up You Wallet' : 'Swap'

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption size="sm" className={styles.description}>
          Perform on-chain swaps within your operational wallet and get rewards!
        </Caption>
      </div>
      <div className={styles.body}>
        <div className={styles.chains}>
          <FormField caption="From" type="custom" size="lg" className={styles.chainSelector}>
            <ChainSelector
              chains={chains}
              className={styles.chain}
              chain={values.chainFrom}
              size="sm"
              onChainChange={handleChangeChainFromValue}
            />
          </FormField>
          <Button
            size="lg"
            variant="clear"
            icon={<IconChange className={styles.changeIcon} />}
            className={styles.change}
            onClick={handleChangeChains}
          />
          <FormField caption="To" type="custom" size="lg" className={styles.chainSelector}>
            <ChainSelector
              chains={chains}
              className={styles.chain}
              chain={values.chainTo}
              size="sm"
              onChainChange={handleChangeChainToValue}
            />
          </FormField>
        </div>

        <Display
          className={styles.display}
          caption="You pay"
          header={
            <div className={styles.aside}>
              <Show if={balanceFrom}>
                <div className={styles.options}>
                  <Button
                    caption="25%"
                    isOutline
                    size="xxs"
                    className={styles.option}
                    onClick={handleChangeAmountPercent(0.25)}
                  />
                  <Button
                    caption="50%"
                    isOutline
                    size="xxs"
                    className={styles.option}
                    onClick={handleChangeAmountPercent(0.5)}
                  />
                  <Button
                    caption="MAX"
                    isOutline
                    size="xxs"
                    className={styles.option}
                    onClick={handleChangeAmountPercent(1)}
                  />
                </div>
              </Show>

              {renderBalance(balanceFrom)}
            </div>
          }>
          <div className={styles.asset}>
            <TokenSelector
              includeNative
              placeholder="Search token"
              className={styles.tokenSelector}
              chains={[values.chainFrom]}
              token={
                {
                  ...values.tokenFrom,
                  network: values.chainFrom.name,
                } as TokenV3Model
              }
              account={wallet || undefined}
              onTokenChange={handleChangeTokenFromValue}
            />

            <label className={styles.amount}>
              <input
                className={styles.input}
                value={values.amountValue}
                placeholder="0"
                inputMode="numeric"
                onFocus={handleFocus}
                onChange={handleChangeAmountValue}
              />
              <Value
                className={styles.value}
                value={formatNumber((values.tokenFrom.priceUSD || 0) * (values.amount || 0))}
                prefix="$"
              />
            </label>
          </div>
        </Display>

        <Display
          className={styles.display}
          caption="You receive"
          header={<div className={styles.aside}>{renderBalance(balanceTo)}</div>}
          footer={
            !values.tokenTo.verified ? (
              <Caption size="sm" className={styles.warning}>
                Watch out! This token is not verified.
              </Caption>
            ) : null
          }>
          <div className={styles.asset}>
            <TokenSelector
              includeNative
              placeholder="Search token"
              className={styles.tokenSelector}
              chains={[values.chainTo]}
              token={
                {
                  ...values.tokenTo,
                  network: values.chainTo.name,
                } as TokenV3Model
              }
              account={wallet || undefined}
              onTokenChange={handleChangeTokenToValue}
            />

            <div className={styles.amount}>
              <span className={styles.input}>{formatNumber(amountTo)}</span>
              <Value
                className={styles.value}
                value={formatNumber((values.tokenTo.priceUSD || 0) * (amountTo || 0))}
                prefix="$"
              />
            </div>
          </div>
        </Display>

        <Card className={styles.settings}>
          <FormField
            type="switch"
            caption="Advanced Settings"
            onValueChange={handleChangeIsShowSettings}
            defaultChecked={values.isShowSettings}
          />
          <Show if={values.isShowSettings}>
            <TaskFormCustomSwapTokenSlippage
              options={[0.2, 0.5]}
              value={values.slippage}
              className={styles.slippages}
              onValueChange={handleChangeSlippageValue}
            />
          </Show>
        </Card>

        <TaskFormCustomSwapTokenSummary className={styles.summary} reward={50} {...values} />
      </div>

      <div className={styles.footer}>
        <Button
          href={isInsufficientBalance ? '/topup' : undefined}
          caption={buttonCaption}
          size="xl"
          variant="primary"
          isBlock
          isDisabled={!values.amount}
          onClick={!isInsufficientBalance ? handleConfirm : undefined}
        />
      </div>
    </div>
  )
}

export default TaskFormCustomSwapToken
