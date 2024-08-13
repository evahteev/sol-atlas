'use client'

import { FC, PropsWithChildren } from 'react'

import { useWeb3Modal } from '@web3modal/wagmi/react'
import { useAccount } from 'wagmi'

import Button from '@/components/Button'
import Panel from '@/components/Panel'
import Logo from '@/images/logo.svg'

import styles from './wallet.module.scss'

type WalletConnectedProviderProps = PropsWithChildren & {
  //
}

const WalletConnectedProvider: FC<WalletConnectedProviderProps> = ({ children }) => {
  const { address } = useAccount()
  const { open } = useWeb3Modal()

  const handleConnect = () => {
    open()
  }

  if (!address) {
    return (
      <div className={styles.container}>
        <Panel
          className={styles.panel}
          caption="Guru Faucet"
          footer={
            <>
              <Button size="lg" variant="primary" onClick={handleConnect}>
                Connect
              </Button>
            </>
          }>
          <Logo className={styles.image} />
        </Panel>
      </div>
    )
  }

  return children
}

export default WalletConnectedProvider
