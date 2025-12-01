'use client'

import Link from 'next/link'

import { FC, memo, useContext, useMemo, useState } from 'react'

import clsx from 'clsx'
import { Address } from 'viem'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import Loader from '@/components/atoms/Loader'
import Value from '@/components/atoms/Value'
import Dropdown from '@/components/composed/Dropdown'
import Profile from '@/components/feature/Profile'
import Dialog from '@/components/ui/Dialog'
import Show from '@/components/ui/Show'
import useAuth from '@/hooks/useAuth'
import { useSession } from '@/hooks/useAuth.compat'
import { useProfileBalance } from '@/hooks/useProfileBalance'
import { WalletType, useWalletAddress } from '@/hooks/useWalletAddress'
import IconExternal from '@/images/icons/arrow-up-right.svg'
import IconDiscord from '@/images/socials/discord.svg'
import IconTelegram from '@/images/socials/telegram.svg'
import IconX from '@/images/socials/x.svg'
import IconYoutube from '@/images/socials/youtube.svg'
import { ChainModel } from '@/models/chain'
import { AppContext } from '@/providers/context'
import { formatNumber } from '@/utils/numbers'

import LoginButton from '../LoginButton'

import styles from './ProfileBar.module.scss'

type ProfileBarProps = {
  className: string
  chains: ChainModel[]
}

const ProfileMemo = memo(
  Profile,
  (prevProps, newProps) => JSON.stringify(prevProps) === JSON.stringify(newProps)
)

export const ProfileBar: FC<ProfileBarProps> = ({ className, chains }) => {
  const walletAddress = useWalletAddress(WalletType.guru)
  const profileBalance = useProfileBalance(walletAddress as Address)
  const {
    config: { pointsToken, socials },
  } = useContext(AppContext)

  const { data: session } = useSession()
  const { isAuth, isLoading } = useAuth()

  const [isOpen, setIsOpen] = useState(false)

  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  const profileContent = useMemo(
    () => (
      <ProfileMemo
        className={styles.profile}
        chains={chains}
        onClose={handleClose}
        session={session}
      />
    ),
    [chains, session]
  )

  return (
    <>
      <div className={clsx(styles.container, className)} id="profile-bar">
        <div className={styles.personal}>
          <Dropdown caption="Join Us" className={styles.joinus} placement="bottom-end">
            <div className={styles.socials}>
              <ul className={styles.list}>
                {socials?.NEXT_PUBLIC_SOCIAL_TELEGRAM && (
                  <li className={styles.item}>
                    <Link
                      href={socials?.NEXT_PUBLIC_SOCIAL_TELEGRAM ?? ''}
                      target="_blank"
                      className={styles.social}>
                      <IconTelegram className={styles.icon} />
                      <span className={styles.caption}>Telegram</span>
                      <IconExternal className={styles.indicator} />
                    </Link>
                  </li>
                )}
                {socials?.NEXT_PUBLIC_SOCIAL_X && (
                  <li className={styles.item}>
                    <Link
                      href={socials?.NEXT_PUBLIC_SOCIAL_X ?? ''}
                      target="_blank"
                      className={styles.social}>
                      <IconX className={styles.icon} />
                      <span className={styles.caption}>X/Twitter</span>
                      <IconExternal className={styles.indicator} />
                    </Link>
                  </li>
                )}
                {socials?.NEXT_PUBLIC_SOCIAL_DISCORD && (
                  <li className={styles.item}>
                    <Link
                      href={socials?.NEXT_PUBLIC_SOCIAL_DISCORD ?? ''}
                      target="_blank"
                      className={styles.social}>
                      <IconDiscord className={styles.icon} />
                      <span className={styles.caption}>Discord</span>
                      <IconExternal className={styles.indicator} />
                    </Link>
                  </li>
                )}
                {socials?.NEXT_PUBLIC_SOCIAL_YOUTUBE && (
                  <li className={styles.item}>
                    <Link
                      href={socials?.NEXT_PUBLIC_SOCIAL_YOUTUBE ?? ''}
                      target="_blank"
                      className={styles.social}>
                      <IconYoutube className={styles.icon} />
                      <span className={styles.caption}>YouTube</span>
                      <IconExternal className={styles.indicator} />
                    </Link>
                  </li>
                )}
              </ul>
            </div>
          </Dropdown>
          <Show if={!isAuth && !isLoading}>
            <LoginButton className={styles.connect} isOutline />
          </Show>
          <Show if={!isAuth && isLoading}>
            <Loader className={styles.loader} />
          </Show>
          <Show if={isAuth}>
            <div className={styles.balances}>
              <Value
                className={styles.balance}
                value={profileBalance.testnet === null ? '–' : formatNumber(profileBalance.testnet)}
                suffix={` ${pointsToken.symbols[0]}`}
              />
            </div>

            <button className={styles.toggle} onClick={handleOpen}>
              <JazzIcon
                size={48}
                seed={jsNumberForAddress(walletAddress ?? '')}
                className={styles.avatar}
              />
            </button>
          </Show>
        </div>
      </div>

      <Dialog
        type="drawer"
        variant="dark"
        isOpen={isOpen}
        onClose={handleClose}
        className={styles.dialog}>
        {profileContent}
      </Dialog>
    </>
  )
}
