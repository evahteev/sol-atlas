import { PropsWithChildren } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerTokensMarquee } from './_components/marquee/marquee'

import styles from './_assets/page.module.scss'

export const dynamic = 'force-dynamic'

export default async function LayoutTokensExplorer({ children }: PropsWithChildren) {
  const chains = await await fetchChainList().then((res) => res ?? [])

  return (
    <>
      <TokensExplorerTokensMarquee chains={chains} className={styles.marquee} />

      {children}
    </>
  )
}
