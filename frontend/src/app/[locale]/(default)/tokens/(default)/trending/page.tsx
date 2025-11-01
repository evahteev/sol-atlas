import { FC } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerTrending } from '../_components/tokens/trending/trending'

import styles from '../_assets/page.module.scss'

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const chains = await fetchChainList().then((res) => res ?? [])

  return <TokensExplorerTrending className={styles.table} chains={chains} />
}

export default PageTokensExplorer
