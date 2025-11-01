import get from 'lodash/get'
import { env } from 'next-runtime-env'

import auth from '@/auth'
import Banner from '@/components/composed/Banner'
import StateMessage from '@/components/composed/StateMessage'
import IconAI from '@/images/icons/aichat.svg'
import IconFolder from '@/images/icons/folder.svg'
import IconGlobe from '@/images/icons/globe.svg'
import IconTGChat from '@/images/icons/telegram-chat.svg'
import IconTG from '@/images/icons/telegram.svg'
import IconX from '@/images/icons/x.svg'
import IconDiscord from '@/images/socials/discord.svg'
import IconYoutube from '@/images/socials/youtube.svg'
import { FlowClientObject } from '@/services/flow'
import { getWarehouseQueryResponse } from '@/services/warehouse-redash'

import ImageSupport from './_assets/support.svg'
import { PageCommunityConfig } from './_components/config'
import { PageCommunityDashboard } from './_components/dashboard'
import { PageAdminList } from './_components/list/list'
import { PageCommunityWallet } from './_components/wallet'

import styles from './_assets/page.module.scss'

const APP_CONFIG_KEY = 'app_config'

const S3Logo = env('NEXT_PUBLIC_APP_LOGO')

export default async function PageCommunity() {
  const session = await auth()
  const appConfig = await FlowClientObject.config.get({ key: APP_CONFIG_KEY })

  const isAdmin = session?.user?.is_admin
  if (!isAdmin) {
    return (
      <StateMessage type="danger" caption="Forbidden" className={styles.error}>
        You do not have access to this page.
      </StateMessage>
    )
  }
  if (!appConfig) {
    return (
      <StateMessage type="danger" caption="Warning" className={styles.error}>
        This App has no config
      </StateMessage>
    )
  }

  const {
    app_url,
    app_name,
    app_description,
    bot_name,
    support_url = undefined,
    socials,
  } = appConfig.value

  const stats = await getWarehouseQueryResponse('admin_panel_combined', {}, 30 * 60)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <PageCommunityConfig
          className={styles.config}
          caption={app_name}
          description={app_description}
          imageURL={S3Logo || '.'}
          props={{
            link: {
              icon: <IconFolder className={styles.icon} />,
              caption: 'App Link:',
              value: app_url,
              type: 'url',
            },
            bot: {
              icon: <IconAI className={styles.icon} />,
              caption: 'AI Assistant Bot:',
              value: `https://t.me/${bot_name}`,
              type: 'url',
            },
            support: {
              icon: <IconGlobe className={styles.icon} />,
              caption: 'App User Support:',
              value: support_url || '/run/app_support',
              type: 'url',
            },
            // content: {
            //   icon: <IconFolder className={styles.icon} />,
            //   caption: 'Dashboard and Content Management',
            //   type: 'content',
            // },
          }}
        />
      </div>

      <main className={styles.body}>
        <PageCommunityDashboard initialData={stats ?? undefined} className={styles.dashboard} />
        <PageCommunityConfig
          className={styles.config}
          caption="Community Links"
          description="Complete these steps to set up your application."
          props={{
            telegram_chat: {
              icon: <IconTGChat className={styles.icon} />,
              caption: 'Telegram Chat:',
              value: get(socials, 'telegram_chat'),
              type: 'url',
            },
            telegram_channel: {
              icon: <IconTG className={styles.icon} />,
              caption: 'Telegram Channel:',
              value: get(socials, 'telegram_channel'),
              type: 'url',
            },
            discord: {
              icon: <IconDiscord className={styles.icon} />,
              caption: 'Discord:',
              value: get(socials, 'discord'),
              type: 'url',
            },
            youtube: {
              icon: <IconYoutube className={styles.icon} />,
              caption: 'Youtube:',
              value: get(socials, 'youtube'),
              type: 'url',
            },
            x: {
              icon: <IconX className={styles.icon} />,
              caption: 'X (Twitter):',
              value: get(socials, 'x'),
              type: 'url',
            },
          }}
        />

        <PageAdminList className={styles.list} />
      </main>

      <aside className={styles.footer}>
        <PageCommunityWallet className={styles.wallet} />

        <Banner
          caption="User Support"
          image={<ImageSupport />}
          actions={[
            {
              caption: 'Open Ops Chat',
              href: '/flow/app_support',
              isOutline: true,
              variant: 'secondary',
            },
          ]}>
          All support requests from your app&apos;s users will be sent to this Telegram group.
          <hr />
          Our Ops team is also in this group to help with complex issues.
        </Banner>
      </aside>
    </div>
  )
}
