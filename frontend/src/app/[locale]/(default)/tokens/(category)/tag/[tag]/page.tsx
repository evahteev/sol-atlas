import { FC } from 'react'

import { fetchChainList, fetchTokenTags } from '@/actions/tokens'
import StateMessage from '@/components/composed/StateMessage'

import { TokensExplorerTable } from './_components/table/table'

import styles from './_assets/page.module.scss'

type Params = Promise<{ tag: string }>

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC<{ params?: Params }> = async ({ params }) => {
  const [tagsList, chains] = await Promise.all([
    (await fetchTokenTags()) ?? undefined,
    await fetchChainList().then((res) => res ?? []),
  ])

  const searchParams = await params
  const selectedTag = tagsList?.find(
    (item) => item.id === decodeURIComponent(searchParams?.tag || '')
  )

  if (!selectedTag) {
    return <StateMessage type="danger" caption="No token tag found!" />
  }

  return <TokensExplorerTable tag={selectedTag} className={styles.table} chains={chains} />
}

export default PageTokensExplorer
