import { PropsWithChildren } from 'react'

import { getTranslations } from 'next-intl/server'

import { fetchChainList, fetchTokenTags } from '@/actions/tokens'
import Caption from '@/components/ui/Caption'

import { TokensExplorerContent } from './_components/content/content'
import { TokensExplorerTabs } from './_components/tabs/tabs'

import styles from './_assets/layout.module.scss'

export const dynamic = 'force-dynamic'

export default async function LayoutTokensExplorerDefault({ children }: PropsWithChildren) {
  const t = await getTranslations('Tokens')
  const [tags, chains] = await Promise.all([
    (await fetchTokenTags()) ?? undefined,
    await fetchChainList().then((res) => res ?? []),
  ])

  return (
    <>
      <Caption variant="header" size="lg" className={styles.title}>
        {t('title')}
      </Caption>

      <TokensExplorerContent className={styles.results} chains={chains} tags={tags}>
        <TokensExplorerTabs />

        <div className={styles.container}>{children}</div>
      </TokensExplorerContent>
    </>
  )
}
