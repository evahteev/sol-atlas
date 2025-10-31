'use client'

import { FC, useMemo, useState } from 'react'

import clsx from 'clsx'
import { Session } from 'next-auth'
import { useWalletDetailsModal } from 'thirdweb/react'

import Loader from '@/components/atoms/Loader'
import AccountActivity from '@/components/composed/ActivitiesList'
import BalancesList from '@/components/composed/BalancesList'
import NFTsList from '@/components/composed/NFTsList'
import StateMessage from '@/components/composed/StateMessage'
import Tabs from '@/components/composed/Tabs'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { thirdwebConnectBaseConfig } from '@/config/thirdweb'
import { WalletType, useWalletAddress } from '@/hooks/useWalletAddress'
import IconReceive from '@/images/icons/arrow-down.svg'
import IconSend from '@/images/icons/arrow-up.svg'
import IconBack from '@/images/icons/chevron-left.svg'
import IconLogout from '@/images/icons/exit.svg'
import IconBuy from '@/images/icons/plus.svg'
import IconRefetch from '@/images/icons/reload.svg'
import IconSettings from '@/images/icons/settings.svg'
import IconSwap from '@/images/icons/swap.svg'
import { ChainModel } from '@/models/chain'

import ProfileAccount from '../ProfileAccount'
import ProfileReceiveForm from './actions/ProfileReceiveForm'
import ProfileSignoutButton from './actions/ProfileSignoutButton'
import { useProfileData } from './hooks/useProfileData'

import styles from './Profile.module.scss'

type ProfileProps = {
  className?: string
  chains: ChainModel[]
  onClose?: () => void
  session: Session | null
}

export const Profile: FC<ProfileProps> = ({ className, chains, onClose, session }) => {
  const [currentTab, setCurrentTab] = useState<'assets' | 'nft' | 'activities'>('assets')
  const [isOpenReceive, setIsOpenReceive] = useState(false)

  const address = useWalletAddress(WalletType.thirdweb_ecosystem)

  const {
    balances,
    isFetchingBalances,
    nfts,
    totalNftCount,
    isFetchingNftBalances,
    actions,
    isFetchingActions,
    refetch,
    isFetching,
  } = useProfileData({
    address,
    chains,
    refetchInterval: 5 * 60 * 1000,
  })

  const { open: openWalletModal } = useWalletDetailsModal()

  const profileAccount = useMemo(
    () => (
      <ProfileAccount
        address={address || ''}
        chains={chains}
        className={styles.account}
        onClick={() => openWalletModal(thirdwebConnectBaseConfig)}
      />
    ),
    [address, chains, openWalletModal]
  )

  if (!session?.user?.id) {
    return null
  }

  const handleOpenReceive = () => {
    setIsOpenReceive(true)
  }

  const handleCloseReceive = () => {
    setIsOpenReceive(false)
  }

  const handleClose = () => {
    onClose?.()
  }

  if (isOpenReceive) {
    return (
      <div className={clsx(styles.container, className)}>
        <div className={styles.header}>
          <strong className={styles.title}>
            <Button
              className={styles.back}
              variant="custom"
              icon={<IconBack />}
              onClick={handleCloseReceive}
              size="xs"
            />
            Receive
          </strong>
        </div>
        <div className={styles.body}>
          <ProfileReceiveForm
            address={`${address}`}
            className={styles.receive}
            onProcessStart={handleClose}
          />
        </div>
      </div>
    )
  }

  const handleRefetch = () => {
    refetch()
  }

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <div className={styles.tools}>
          <ProfileSignoutButton
            caption="Sign Out"
            size="sm"
            className={styles.tool}
            icon={<IconLogout />}
            isOutline
          />

          <Show if={session?.user?.is_admin}>
            <Button
              size="sm"
              variant="custom"
              className={clsx(styles.tool, styles.settings)}
              icon={<IconSettings />}
              href="/admin"
            />
          </Show>
        </div>

        <Show if={address}>{profileAccount}</Show>

        <div className={styles.actions}>
          {address && (
            <Button
              href="/buy"
              icon={<IconBuy />}
              caption="Buy"
              onClick={handleClose}
              variant="primary"
              size="md"
              className={styles.action}
            />
          )}
          {address && (
            <Button
              icon={<IconReceive />}
              caption="Receive"
              onClick={handleOpenReceive}
              variant="primary"
              size="md"
              className={styles.action}
            />
          )}
          <Button
            href="/send"
            icon={<IconSend />}
            caption="Send"
            variant="primary"
            size="md"
            onClick={handleClose}
            className={styles.action}
          />
          <Button
            href="/swap"
            icon={<IconSwap />}
            caption="Swap"
            variant="primary"
            size="md"
            onClick={handleClose}
            className={styles.action}
          />
          <Button
            href="/profile"
            icon={<IconSettings />}
            caption="Profile"
            variant="secondary"
            size="md"
            onClick={handleClose}
            className={styles.action}
          />
        </div>

        <div className={styles.sections}>
          <Tabs
            className={styles.tabs}
            tabs={[
              {
                caption: 'Assets',
                isActive: currentTab === 'assets',
                onClick: () => {
                  setCurrentTab('assets')
                },
              },
              {
                caption: 'NFT',
                isActive: currentTab === 'nft',
                onClick: () => {
                  setCurrentTab('nft')
                },
              },
              {
                caption: 'Activities',
                isActive: currentTab === 'activities',
                onClick: () => {
                  setCurrentTab('activities')
                },
              },
            ]}
          />

          <Button
            caption="Refresh"
            isOutline
            isPending={isFetching}
            icon={<IconRefetch className={clsx(styles.icon, { [styles.loading]: isFetching })} />}
            className={styles.refetch}
            onClick={handleRefetch}
          />
        </div>
      </div>

      <div className={styles.body}>
        <Show if={!!address}>
          <Show if={currentTab === 'assets'}>
            <Show if={!balances?.length && isFetchingBalances}>
              <Loader className={styles.loading}>Fetching balances&hellip;</Loader>
            </Show>

            <Show if={!balances?.length && !isFetchingBalances}>
              <div className={styles.empty}>
                <Caption variant="header" size="lg" className={styles.title}>
                  Your operational wallet is empty
                </Caption>

                <ProfileReceiveForm address={`${address}`} onProcessStart={handleClose} />
              </div>
            </Show>

            <BalancesList
              chains={chains}
              className={clsx(styles.content, {
                [styles.loading]: balances?.length && isFetchingBalances,
              })}
              data={balances}
            />
          </Show>

          <Show if={currentTab === 'nft'}>
            <Show if={!totalNftCount && isFetchingNftBalances}>
              <Loader className={styles.loading}>Fetching NFT data&hellip;</Loader>
            </Show>

            <Show if={!totalNftCount && !isFetchingNftBalances}>
              <StateMessage
                // type="info"
                className={styles.info}
                caption="This account currently has no any NFT"
              />
            </Show>

            <NFTsList
              chains={chains}
              className={clsx(styles.content, {
                [styles.loading]: balances?.length && isFetchingNftBalances,
              })}
              data={nfts}
            />
          </Show>

          <Show if={currentTab === 'activities'}>
            <Show if={!actions.length && isFetchingActions}>
              <Loader className={styles.loading}>Fetching account activity&hellip;</Loader>
            </Show>

            <Show if={!actions.length && !isFetchingActions}>
              <StateMessage
                // type="info"
                className={styles.info}
                caption="This account currently has no any activity"
              />
            </Show>

            <AccountActivity
              address={`${address}`}
              chains={chains}
              className={clsx(styles.content, {
                [styles.loading]: balances?.length && isFetchingActions,
              })}
              data={actions}
            />
          </Show>
        </Show>
      </div>
    </div>
  )
}
