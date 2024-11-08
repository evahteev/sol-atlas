import { PropsWithChildren } from 'react'

import clsx from 'clsx'

import auth from '@/auth'
import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import { Caption, Tab } from '@/components/ui'
import { getShortAddress } from '@/utils/strings'

import { ProfileBackButton } from './_components/backButton'

// import ProfileProperties from './_components/properties'
// import ProfileSocials from './_components/socials'
import styles from './_assets/layout.module.scss'

export default async function LayoutProfile({ children }: PropsWithChildren) {
  const session = await auth()
  const guruWalletAddress = session?.user.web3_wallets.find(
    (x) => x.network_type === 'guru'
  )?.wallet_address

  return (
    <>
      <ProfileBackButton />
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.illustration}>
            {!!guruWalletAddress && (
              <JazzIcon seed={jsNumberForAddress(guruWalletAddress)} className={styles.avatar} />
            )}
            {/* <span className={styles.tag}>TOP</span> */}
          </div>

          <Caption
            variant="header"
            size="md"
            className={clsx(styles.title, { [styles.premium]: true })}>
            {getShortAddress(guruWalletAddress)}
          </Caption>

          {/* <div className={styles.followings}>
          <div className={styles.following}>
            <span className={styles.value}>349</span>{' '}
            <span className={styles.caption}>Following</span>
          </div>
          <div className={styles.following}>
            <span className={styles.value}>24</span>{' '}
            <span className={styles.caption}>Followers</span>
          </div>
        </div>

        <div className={styles.description}>
          <Caption variant="header" size="sm" className={styles.heading}>
            Bio
          </Caption>
          <p>Hey, I’m Artem! In Crypto since 2017</p>
          <p>Founder Burning Mem Ex. AvaLabs / Ex. AT&T Shill me your Memecoin! </p>
        </div> */}
        </div>
        <div className={styles.body}>
          {/* <ProfileSocials
          className={styles.socials}
          items={{ x: '/', telegram: '/', instagram: '/', web: '/' }}
        />

        <ProfileProperties className={styles.stats} />
*/}
          <div className={styles.tabs}>
            {/* <Tab href="/profile" exact={true}>
            Memes
          </Tab>
          <Tab href="/profile/activity" exact={true}>
            Activity
          </Tab>
          <Tab href="/profile/balance" exact={true}>
            Balance
          </Tab> */}
            <Tab href="/profile/wallets" exact={true}>
              Wallets
            </Tab>
          </div>
          {children}
        </div>
      </div>
    </>
  )
}
