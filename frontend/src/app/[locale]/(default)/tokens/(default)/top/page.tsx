import { FC } from 'react'

import { fetchChainList } from '@/actions/tokens'

import { TokensExplorerTopVolume } from '../_components/tokens/topVolume/topVolume'

import styles from '../_assets/page.module.scss'

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const chains = await fetchChainList().then((res) => res ?? [])

  return <TokensExplorerTopVolume className={styles.table} chains={chains} />
}

export default PageTokensExplorer
