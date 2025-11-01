import { FC } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerGainers } from '../_components/tokens/gainers/gainers'

import styles from '../_assets/page.module.scss'

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const chains = await fetchChainList().then((res) => res ?? [])

  return <TokensExplorerGainers className={styles.table} chains={chains} />
}

export default PageTokensExplorer
