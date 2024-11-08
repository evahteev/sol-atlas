'use client'

import { FC, useCallback, useEffect, useState } from 'react'

import clsx from 'clsx'
import useWebSocket, { ReadyState } from 'react-use-websocket'

import { ActionPanel } from '@/components/page'
import { Button, Card } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import IconSwap from '@/images/icons/swap.svg'
import { TokenModel } from '@/models/token'
import { FlowClientObject } from '@/services/flow'

import { PageActionsSwapField } from './_components/field/field'

import styles from './_assets/page.module.scss'

type PageActionsSwapTokenState = {
  token?: TokenModel
  amount: number
}

type PageActionsSwapState = {
  sell: PageActionsSwapTokenState
  buy: PageActionsSwapTokenState
}

const PageActionsSwap: FC = () => {
  const [state, setState] = useState<PageActionsSwapState>({
    sell: { amount: 0 },
    buy: { amount: 0 },
  })

  //Public API that will echo messages sent to it back to the client
  const [socketUrl, setSocketUrl] = useState<string | null>(null)
  const [messageHistory, setMessageHistory] = useState<MessageEvent[]>([])
  const { lastMessage, readyState } = useWebSocket(socketUrl)

  const handleSubmit = useCallback(async () => {
    if (!state.sell.token || !state.buy.token) {
      return
    }
    const instance = await FlowClientObject.engine.process.definitions.start('swap_tokens_uni_v2', {
      variables: {
        token_in: {
          value: state.sell.token.address,
          type: 'String',
        },
        token_out: {
          value: state.buy.token.address,
          type: 'String',
        },
        amount_in: {
          value: state.sell.amount * 10 ** state.sell.token.decimals,
          type: 'Long',
        },
        amount_out: {
          value: state.buy.amount,
          type: 'Long',
        },
        web3_url: {
          value: tGuru.rpcUrls.default.http[0],
          type: 'String',
        },
        wallet_address: {
          value: '0x00a746272a634380B82dDf7630d0772f85eF7b26',
          type: 'String',
        },
        router_address: {
          value: '0x55874c7E85725240092363A96BCcE6996980025F',
          type: 'String',
        },
      },
    })
    setSocketUrl(`${process.env.NEXT_PUBLIC_WAREHOUSE_WS_API}/${instance.id}`)
  }, [state.buy.amount, state.buy.token, state.sell.amount, state.sell.token])

  useEffect(() => {
    if (lastMessage !== null) {
      setMessageHistory((prev) => prev.concat(lastMessage))
    }
  }, [lastMessage])

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState]

  const handleChangeAmountSell = (amount: number) => {
    setState((prevState) => ({
      buy: prevState.buy,
      sell: { token: prevState.sell.token, amount },
    }))
  }

  const handleChangeAmountBuy = (amount: number) => {
    setState((prevState) => ({
      sell: prevState.sell,
      buy: { token: prevState.buy.token, amount },
    }))
  }

  const handleChangeTokenSell = (token: TokenModel) => {
    setState((prevState) => ({
      buy: prevState.buy,
      sell: { amount: prevState.sell.amount, token },
    }))
  }

  const handleChangeTokenBuy = (token: TokenModel) => {
    setState((prevState) => ({
      sell: prevState.sell,
      buy: { amount: prevState.buy.amount, token },
    }))
  }

  const handleSwitch = () => {
    setState((prevState) => ({
      sell: prevState.buy,
      buy: prevState.sell,
    }))
  }

  return (
    <form className={styles.container}>
      <Card className={styles.body}>
        <PageActionsSwapField
          caption="Sell"
          amount={state.sell.amount}
          token={state.sell.token}
          skipToken={state.buy.token}
          onChangeAmount={handleChangeAmountSell}
          onChangeToken={handleChangeTokenSell}
          className={styles.sell}
        />
        <PageActionsSwapField
          caption="Buy"
          amount={state.buy.amount}
          token={state.buy.token}
          skipToken={state.sell.token}
          onChangeAmount={handleChangeAmountBuy}
          onChangeToken={handleChangeTokenBuy}
          className={styles.buy}
        />

        <Button
          className={clsx(styles.switch, {
            [styles.hasTokens]: state.buy.token && state.sell.token,
          })}
          icon={<IconSwap className={styles.icon} />}
          onClick={handleSwitch}
        />
      </Card>

      <ActionPanel className={styles.footer}>
        {/* {address && ( */}
        <Button
          caption="Swap"
          variant="primary"
          size="xl"
          type="button"
          isBlock
          isDisabled={false}
          onClick={handleSubmit}
        />
        {/* )} */}
        {/* {!address && (
          <Button
            caption="Connect Wallet"
            variant="primary"
            size="xl"
            type="submit"
            isBlock
            onClick={() => open()}
          />
        )} */}
      </ActionPanel>

      <span>The WebSocket is currently {connectionStatus}</span>
      {lastMessage ? <span>Last message: {lastMessage.data}</span> : null}
      <ul>
        {messageHistory.map((message, idx) => (
          <span key={idx}>{message ? message.data : null}</span>
        ))}
      </ul>
    </form>
  )
}

export default PageActionsSwap
