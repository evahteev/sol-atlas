'use client'

import { FC, useEffect, useState } from 'react'

import { useWeb3Modal } from '@web3modal/wagmi/react'
import clsx from 'clsx'
import Jazzicon, { jsNumberForAddress } from 'react-jazzicon'
import { useAccount, useBalance } from 'wagmi'

import { getShortAddress } from '@/utils'
import { formatNumber } from '@/utils/numbers'

import Button from '../Button'

import styles from './AppMenu.module.scss'

type AppMenuWalletProps = {
  className?: string
}

export const AppMenuWallet: FC<AppMenuWalletProps> = ({ className }) => {
  const { address } = useAccount()
  const { open } = useWeb3Modal()
  const { data: balance } = useBalance({ address, chainId: 261 })
  const { value, symbol, decimals } = balance ?? {}
  const [currentAddress, setCurrentAddress] = useState<string>()

  useEffect(() => {
    setCurrentAddress(address)
  }, [address])

  const valueNumber = Number(value)

  return (
    <div className={clsx(styles.wallet, className)}>
      <Button
        size="lg"
        variant="primary"
        className={clsx(styles.walletButton, { [styles.walletButtonConnected]: !!currentAddress })}
        onClick={() => open()}>
        <span className={styles.walletContent}>
          <span
            className={clsx(styles.walletCaption, {
              [styles.walletCaptionConnected]: !!currentAddress,
            })}>
            {currentAddress ? (
              <span className={styles.walletAddress}>{getShortAddress(currentAddress)}</span>
            ) : (
              <span className={styles.walletConnect}>Connect</span>
            )}
            {!!value && (
              <span className={styles.walletBalanceValue}>
                {formatNumber(valueNumber / Math.pow(10, decimals ?? 18))} {symbol}
              </span>
            )}
          </span>
          {currentAddress && <Jazzicon diameter={20} seed={jsNumberForAddress(currentAddress)} />}
        </span>
      </Button>
    </div>
  )
}
