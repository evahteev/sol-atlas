import { Metadata } from 'next'

import { FC } from 'react'

import { SeasonPassFaucetTable } from './_table'

import styles from './page.module.scss'

type SeasonPassFaucetProps = {
  //
}

export const metadata: Metadata = {
  title: 'Guru Network Faucet',
}

const SeasonPassFaucet: FC<SeasonPassFaucetProps> = () => {
  return <SeasonPassFaucetTable className={styles.table} />
}

export default SeasonPassFaucet
