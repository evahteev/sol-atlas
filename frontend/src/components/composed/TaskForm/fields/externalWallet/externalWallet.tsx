import { FC } from 'react'

import { useAppKit, useAppKitAccount } from '@reown/appkit/react'
import clsx from 'clsx'

import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'
import { getShortAddress } from '@/utils/strings'

import styles from './externalWallet.module.scss'

type TaskFormFieldExternalWalletProps = {
  className?: string
  name: string
  title?: string | null
}

export const TaskFormFieldExternalWallet: FC<TaskFormFieldExternalWalletProps> = ({
  className,
  name,
  title,
}) => {
  const { open } = useAppKit()
  const { address, isConnected } = useAppKitAccount()

  const handleConnect = () => {
    open()
  }

  return (
    <FormField caption={title} type="custom" className={clsx(styles.container, className)}>
      <Button
        className={styles.button}
        isBlock
        isOutline
        size="lg"
        variant="secondary"
        onClick={handleConnect}
        caption={
          isConnected ? `Connected wallet: ${getShortAddress(address)}` : 'Connect External Wallet'
        }
      />

      <input value={isConnected ? address : ''} name={name} type="hidden" />
    </FormField>
  )
}
