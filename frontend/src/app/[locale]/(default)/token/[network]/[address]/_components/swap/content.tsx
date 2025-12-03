'use client'

import { FC } from 'react'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'
import QuestRunner from '@/components/feature/QuestRunner'
import { useSession } from '@/hooks/useAuth.compat'
import { mapGuruNetworkToChainId } from '@/utils/chains'

import styles from './swap.module.scss'

export type TokenOverviewTokenSwapContentProps = {
  className?: string
  token: CustomToken
}

export const TokenOverviewTokenSwapContent: FC<TokenOverviewTokenSwapContentProps> = ({
  token,
  className,
}) => {
  const { data: session } = useSession()

  return (
    <QuestRunner
      processDefinitionKey="swap_tokens_from_external_wallet"
      businessKey={`${session?.user?.id}-${token.id}`}
      className={className}
      startVariables={{
        token_buy: { value: token.id, type: 'String' },
        dst_chain_id: { value: mapGuruNetworkToChainId[token.network], type: 'String' },
        chain_id: { value: mapGuruNetworkToChainId[token.network], type: 'String' },
      }}
      isStartable
      content={{
        loader: <Loader className={styles.loader}>Warming up&hellip;</Loader>,
        starter: <Loader className={styles.loader}>Starting swap&hellip;</Loader>,
        waiting: <Loader className={styles.loader}>One moment&hellip;</Loader>,
        empty: (
          <StateMessage
            type="danger"
            className={styles.message}
            caption="Swap is not available at the moment."
          />
        ),
      }}
    />
  )
}
