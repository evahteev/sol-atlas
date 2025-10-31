import { FC } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerLosers } from '../_components/tokens/losers/losers'

import styles from '../_assets/page.module.scss'

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const chains = await fetchChainList().then((res) => res ?? [])

  return <TokensExplorerLosers className={styles.table} chains={chains} />
}

export default PageTokensExplorer
