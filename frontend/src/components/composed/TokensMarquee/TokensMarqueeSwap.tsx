'use client'

import { FC, useState } from 'react'

import { useSession } from 'next-auth/react'

import Delta from '@/components/atoms/Delta'
import Loader from '@/components/atoms/Loader'
import TokenAsset from '@/components/atoms/TokenAsset'
import QuestRunner from '@/components/feature/QuestRunner'
import Dialog from '@/components/ui/Dialog'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { mapGuruNetworkToChainId } from '@/utils/chains'

import StateMessage from '../StateMessage'

import styles from './TokensMarquee.module.scss'

type TokensMarqueeSwapProps = {
  token: Pick<TokenV3Model, 'address' | 'logoURI' | 'network' | 'symbols' | 'priceUSDChange24h'>
  network?: Pick<ChainModel, 'name' | 'color'>
}

export const TokensMarqueeSwap: FC<TokensMarqueeSwapProps> = ({ token, network }) => {
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
      <span className={styles.swap} onClick={handleOpen}>
        <TokenAsset
          hideNetwork
          logo={token?.logoURI}
          symbol={token.symbols}
          network={network ?? { name: 'UNKN' }}
          size="sm"
        />
        <Delta value={token?.priceUSDChange24h * 100} />
      </span>

      <Dialog isOpen={isOpen} onClose={handleClose} isMaximized className={styles.dialog}>
        <QuestRunner
          processDefinitionKey="swap_tokens"
          businessKey={`${session?.user?.id}-${token.address}-${token.network}`}
          className={styles.body}
          startVariables={{
            token_buy: { value: `${token.address}-${token.network}`, type: 'String' },
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
