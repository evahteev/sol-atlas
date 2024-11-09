'use client'

import { FC, useState } from 'react'

import { Button, Caption } from '@/components/ui'
import Dialog from '@/components/ui/Dialog'
import IconMore from '@/images/icons/more.svg'

import styles from './remove.module.scss'

type ProfileWalletsAddressRemoveProps = {
  address: string
}

export const ProfileWalletsAddressRemove: FC<ProfileWalletsAddressRemoveProps> = () => {
  const [isOpen, setIsOpen] = useState(false)

  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  return (
    <>
      <button className={styles.toggle} onClick={handleOpen}>
        <IconMore className={styles.icon} />
      </button>

      <Dialog isOpen={isOpen} className={styles.modal} onClose={handleClose}>
        <div className={styles.container}>
          <div className={styles.header}>
            <Caption variant="header" size="lg" className={styles.title}>
              Are you sure you want to disable this wallet?
            </Caption>
          </div>
          <div className={styles.footer}>
            <Button size="xl" variant="danger" isBlock>
              Yes, I want to turn it off
            </Button>
            <Button size="xl" isBlock onClick={handleClose}>
              Cancel
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  )
}
