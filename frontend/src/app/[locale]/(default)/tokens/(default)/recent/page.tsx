import { FC } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerRecent } from '../_components/tokens/recent/recent'

import styles from '../_assets/page.module.scss'

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const chains = await fetchChainList().then((res) => res ?? [])

  return <TokensExplorerRecent className={styles.table} chains={chains} />
}

export default PageTokensExplorer
