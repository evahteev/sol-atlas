import clsx from 'clsx'

import { fetchChainList, fetchTokens } from '@/actions/tokens'
import StateMessage from '@/components/composed/StateMessage'
import Copy from '@/components/ui/Copy'
import Tab from '@/components/ui/Tab'
import { getShortAddress } from '@/utils/strings'

import TokenActivity from './_components/activity'
import { TokenAIChat } from './_components/aiChat/aiChat'
import { PageTokenAsset } from './_components/asset/asset'
import { PageTokenChart } from './_components/chart/chart'
import { TokenOverviewLinks } from './_components/links'
import PageTokenShareButton from './_components/share/share'
import TokenOverviewStats from './_components/stats'
import { TokenOverviewTokenSwapContent } from './_components/swap/content'
import { TokenOverviewTokenSwap } from './_components/swap/swap'

import styles from './_assets/page.module.scss'

type Params = Promise<{ network: string; address: string }>
type SearchParams = Promise<{ view: string }>

const PageToken = async ({
  params,
  searchParams,
}: {
  params: Params
  searchParams: SearchParams
}) => {
  const { network, address } = await params
  const { view = '' } = await searchParams

  const tokens = await fetchTokens({ ids: [`${address.toLowerCase()}-${network}`] })
  const token = tokens?.[0]

  if (!token) {
    return <StateMessage type="danger" caption="No token found" />
  }

  const chains = await fetchChainList().then((res) => res ?? [])

  const isDefaultTab = !['details', 'activity'].includes(view)

  return (
    <>
      <TokenAIChat prompts={[]} entry={{ type: 'token', id: token.id }} />
      <div className={styles.header}>
        <PageTokenAsset token={token} chains={chains ?? []} className={styles.asset} />

        <div className={styles.info}>
          <span className={styles.address}>
            {getShortAddress(token.address)}

            <Copy text={token.address} className={styles.copy} />
          </span>
          <TokenOverviewLinks chains={chains ?? []} token={token} />
        </div>

        <div className={styles.tabs}>
          <Tab
            href={`?`}
            isActive={isDefaultTab}
            className={clsx(styles.tab, styles.tabChart, { [styles.tabActive]: isDefaultTab })}>
            Chart
          </Tab>
          <Tab
            href={{ query: { view: 'details' } }}
            isActive={view === 'details'}
            className={clsx(styles.tab, styles.tabStats, {
              [styles.tabActive]: view === 'details',
            })}>
            Details
          </Tab>
          <Tab
            href={{ query: { view: 'activity' } }}
            isActive={view === 'activity'}
            className={clsx(styles.tab, styles.tabActivity, {
              [styles.tabActive]: view === 'activity',
            })}>
            Activity
          </Tab>
        </div>

        <TokenOverviewTokenSwap
          token={token}
          caption="Swap"
          size="sm"
          className={clsx(styles.tool, styles.swap)}
        />
        <PageTokenShareButton token={token} isOutline className={clsx(styles.tool, styles.share)} />
      </div>

      <div className={styles.body}>
        <div className={clsx(styles.chart, { [styles.active]: isDefaultTab })}>
          <PageTokenChart className={styles.chartContent} token={token} chains={chains ?? []} />
        </div>

        <div className={clsx(styles.stats, { [styles.active]: view === 'details' })}>
          <TokenOverviewStats token={token} className={styles.statsContent} />
        </div>

        <div className={clsx(styles.activity, { [styles.active]: view === 'activity' })}>
          <TokenActivity token={token} className={styles.activityContent} chains={chains} />
        </div>

        <div className={clsx(styles.swap, { [styles.active]: view === 'activity' })}>
          <TokenOverviewTokenSwapContent token={token} className={styles.swapContent} />
        </div>
      </div>
    </>
  )
}

export default PageToken
