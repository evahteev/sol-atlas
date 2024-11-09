import { FC, ReactNode } from 'react'

import clsx from 'clsx'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import { Caption, Show } from '@/components/ui'
import { getShortAddress } from '@/utils/strings'

import styles from './address.module.scss'

type ProfileWalletsAddress = {
  className?: string
  address: string
  action?: ReactNode
}

export const ProfileWalletsAddress: FC<ProfileWalletsAddress> = ({
  className,
  address,
  action,
}) => {
  return (
    <div className={clsx(styles.container, className)}>
      <JazzIcon size={32} seed={jsNumberForAddress(address)} className={styles.avatar} />

      <Caption variant="body" size="md" strong>
        {getShortAddress(address)}
      </Caption>

      <Show if={action}>
        <div className={styles.action}>{action}</div>
      </Show>
    </div>
  )
}
