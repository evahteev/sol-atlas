'use client'

import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Copy from '@/components/ui/Copy'
import Show from '@/components/ui/Show'
import IconLink from '@/images/icons/link.svg'
import IconSettings from '@/images/icons/settings.svg'
import IconTelegram from '@/images/icons/telegram.svg'
import { Session } from '@/lib/session'
import { getShortAddress } from '@/utils/strings'

import styles from './profile.module.scss'

type ProfileTranslations = {
  title: string
  adminPanel: string
}

type UserProfileSectionProps = {
  className?: string
  session: Session | null
  walletAddress?: string
  translations: ProfileTranslations
}

export const PageAIFeedProfile: FC<UserProfileSectionProps> = ({
  className,
  session,
  walletAddress,
  translations,
}) => {
  if (!session?.user) {
    return null
  }

  return (
    <Card className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <Caption variant="header" size="md" className={styles.title}>
          {translations.title}
        </Caption>
      </div>

      <div className={styles.body}>
        <div className={styles.profile}>
          <JazzIcon
            size={48}
            seed={jsNumberForAddress(walletAddress || '0x0000000000000000000000000000000000000000')}
            className={styles.avatar}
          />

          <div className={styles.props}>
            {walletAddress && (
              <div className={styles.prop}>
                <div className={styles.propValue}>
                  <IconLink className={styles.propIcon} />

                  <span className={styles.caption}>{getShortAddress(walletAddress)}</span>
                </div>

                <Copy className={styles.copy} text={walletAddress} size="md" />
              </div>
            )}

            <Show if={session.user.telegram_user_id}>
              <span className={styles.prop}>
                <Link
                  className={clsx(styles.propValue, styles.link)}
                  href={`tg://user?id=${session.user.telegram_user_id}`}>
                  <IconTelegram className={styles.propIcon} />
                  {session.user.telegram_user_id}
                </Link>
                <Copy
                  className={styles.copy}
                  text={`${session.user.telegram_user_id || ''}`}
                  size="md"
                />
              </span>
            </Show>
          </div>
        </div>
      </div>

      <Show if={session.user.is_admin}>
        <div className={styles.footer}>
          {session.user.is_admin && (
            <Button
              href="/admin"
              variant="secondary"
              size="sm"
              icon={<IconSettings />}
              caption={translations.adminPanel}
              className={styles.action}
            />
          )}
        </div>
      </Show>
    </Card>
  )
}
