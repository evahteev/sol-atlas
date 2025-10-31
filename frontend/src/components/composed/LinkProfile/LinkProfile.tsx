import { useCallback, useEffect, useMemo } from 'react'

import clsx from 'clsx'
import { useSession } from 'next-auth/react'
import { toast } from 'react-toastify'
import { useLinkProfile, useProfiles } from 'thirdweb/react'

import Button, { ButtonProps } from '@/components/ui/Button'
import { client } from '@/config/thirdweb'
import IconSuccess from '@/images/icons/success.svg'
import IconTelegram from '@/images/socials/telegram.svg'
import IconX from '@/images/socials/x.svg'
import { FlowClientObject } from '@/services/flow'

import LoginButton from '../LoginButton'

import styles from './LinkProfile.module.scss'

export type LinkProfileProps = ButtonProps & {
  social: 'telegram' | 'x' | 'google'
  onSuccess?: (details: { id?: string; username?: string }) => void
}

function LinkProfile({
  className,
  social,
  onSuccess,
  caption = 'Link Profile',
  ...buttonProps
}: LinkProfileProps) {
  const { data: session } = useSession()

  const { data: profiles } = useProfiles({
    client,
  })

  const { mutate: linkProfile, isPending, data, isSuccess, error } = useLinkProfile()
  const updateTelegram = useCallback(
    async ({ id, username }: { id: string; username: string }) => {
      if (!session?.user?.webapp_user_id) return
      // @ts-expect-error types
      await FlowClientObject.user.update({
        telegram_user_id: parseInt(id),
        username,
        webapp_user_id: session?.user?.webapp_user_id,
      })
    },
    [session]
  )

  const isLinked = useMemo(() => {
    if (social === 'telegram') {
      return !!session?.user?.telegram_user_id
    }
    if (profiles?.length) {
      const socialProfile = profiles.find((x) => x.type === social)
      if (socialProfile) {
        return true
      }
    }
    return false
  }, [profiles, session?.user?.telegram_user_id, social])

  useEffect(() => {
    if (error) {
      toast.error(error.message)
    }
  }, [error])

  // eagerly invoke onSuccess when profile is found to be linked
  useEffect(() => {
    if (profiles?.length) {
      const socialProfile = profiles.find((x) => x.type === social)
      if (socialProfile) {
        onSuccess?.(socialProfile.details)
      }
    }
  }, [onSuccess, profiles, social])

  useEffect(() => {
    if (isSuccess) {
      const profile = data.find((item) => item.type === social)
      if (profile) {
        toast.success('Profile linked successfully')
        onSuccess?.(profile.details)
        // @ts-expect-error thirdweb types for link profiles
        const { id, username } = profile.details
        if (social === 'telegram' && id && username) {
          updateTelegram({ id, username })
        }
      }
    }
  }, [isSuccess, data, social, onSuccess, updateTelegram])

  const onClick = () => {
    if (isPending || isLinked) {
      return
    }
    linkProfile({
      client,
      strategy: social,
    })
  }
  return (
    <div className={clsx(styles.container, className)}>
      <LoginButton className={styles.login} />
      <Button
        className={styles.button}
        onClick={onClick}
        {...buttonProps}
        isPending={isPending}
        icon={
          isLinked ? (
            <IconSuccess className={styles.icon} />
          ) : social === 'telegram' ? (
            <IconTelegram className={styles.icon} />
          ) : social === 'x' ? (
            <IconX className={styles.icon} />
          ) : undefined
        }
        caption={isLinked ? 'Linked Successfully' : caption}
      />
    </div>
  )
}

export default LinkProfile
