'use client'

import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode, useState } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'
import { env } from 'next-runtime-env'
import { base } from 'thirdweb/chains'
import { ConnectEmbed, useActiveWalletChain } from 'thirdweb/react'

import Loader from '@/components/atoms/Loader'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import { thirdwebConnectBaseConfig } from '@/config/thirdweb'
import useAuth from '@/hooks/useAuth'
import { useClientOnce } from '@/hooks/useClientOnce'
import { useConnectHandler } from '@/hooks/useConnectHandler'
import IconGuruLogo from '@/images/gurunetwork/mainnet.svg'

import styles from './RequireLogin.module.scss'

type RequireLoginProps = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  caption?: ReactNode
  isRequired?: boolean
}

export const RequireLogin: FC<RequireLoginProps> = ({
  className,
  children,
  caption,
  isRequired = true,
  ...props
}) => {
  const t = useTranslations('Auth')
  const { onConnectHandler } = useConnectHandler()
  const chain = useActiveWalletChain()
  const [isClient, setIsClient] = useState(false)
  const { isAuth, isLoading } = useAuth()

  useClientOnce(() => {
    setIsClient(true)
  })

  if (!isRequired || isAuth) {
    return children
  }

  if (!isClient || isLoading) {
    return <Loader className={clsx(styles.loader, className)} />
  }

  const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'
  const effectiveCaption = caption || t('welcome', { appName })

  return (
    <Card {...props} className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <div className={styles.logo}>
          <IconGuruLogo />
        </div>

        <Caption variant="header" size="lg" className={styles.title}>
          {effectiveCaption}
        </Caption>
        <Caption variant="body" size="lg" className={styles.title}>
          {t('description')}
        </Caption>
      </div>

      <div className={styles.body}>
        <ConnectEmbed
          {...thirdwebConnectBaseConfig}
          onConnect={onConnectHandler}
          accountAbstraction={{
            chain: base,
            sponsorGas: chain?.id === base.id,
          }}
        />
      </div>
    </Card>
  )
}
