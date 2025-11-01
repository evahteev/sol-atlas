'use client'

import { FC, useState } from 'react'

import clsx from 'clsx'
import { useSession } from 'next-auth/react'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'
import QuestRunner from '@/components/feature/QuestRunner'
import Button, { ButtonProps } from '@/components/ui/Button'
import Dialog from '@/components/ui/Dialog'
import IconSwap from '@/images/icons/swap.svg'
import { mapGuruNetworkToChainId } from '@/utils/chains'

import styles from './swap.module.scss'

type TokenOverviewTokenSwapProps = ButtonProps & {
  token: CustomToken
  isSelectable?: boolean
}

export const TokenOverviewTokenSwap: FC<TokenOverviewTokenSwapProps> = ({
  variant,
  size,
  token,
  className,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { data: session } = useSession()
  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  return (
    <>
      <Button
        {...props}
        variant={variant ?? 'primary'}
        size={size ?? 'sm'}
        className={clsx(styles.action, className)}
        icon={<IconSwap className={clsx(styles.icon, styles.swap)} />}
        onClick={handleOpen}
      />

      <Dialog isOpen={isOpen} onClose={handleClose} isMaximized className={styles.dialog}>
        <QuestRunner
          processDefinitionKey="swap_tokens"
          businessKey={`${session?.user?.id}-${token.id}`}
          className={styles.body}
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
      </Dialog>
    </>
  )
}
