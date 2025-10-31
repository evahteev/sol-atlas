import clsx from 'clsx'

import Text from '@/components/atoms/Text'
import Caption from '@/components/ui/Caption'

import { PageLauncherCTA } from './_components/cta'
import { PageLauncherDashboard } from './_components/dashboard'

import styles from './_assets/page.module.scss'

export const revalidate = 300

export default async function PageLauncher() {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="header" size="lg" className={styles.title}>
          Launcher Wizard
        </Caption>
      </div>

      <div className={styles.body}>
        <PageLauncherCTA
          className={styles.cta}
          caption="Explore the GURU Community App Ecosystem"
          action={{
            caption: 'Launch Your App',
            variant: 'success',
            size: 'lg',
            href: '/flow/token_app',
          }}>
          <Text>
            <p>
              Every app you see here was launched with the GURU Framework Wizard—no code needed.
              They all run on our powerful automation, AI, and Web3 infrastructure. Ready to add
              your app to the list?
            </p>
          </Text>
        </PageLauncherCTA>

        <PageLauncherDashboard />

        <PageLauncherCTA
          className={clsx(styles.cta, styles.last)}
          caption="The ultimate upgrade for your community"
          action={{
            caption: 'Launch Your App',
            variant: 'success',
            size: 'lg',
            href: '/flow/token_app',
          }}>
          <Text>
            <p>
              Launch your unique app under 5 mins and start your journey in the GURU ecosystem
              today.
            </p>
          </Text>
        </PageLauncherCTA>
      </div>
    </div>
  )
}
