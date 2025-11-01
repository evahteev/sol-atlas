import { base } from 'thirdweb/chains'
import { PayEmbed } from 'thirdweb/react'

import { client } from '@/config/thirdweb'

import styles from './_assets/page.module.scss'

export default async function PageBuyGuru() {
  return (
    <div className={styles.container}>
      <PayEmbed
        className={styles.body}
        client={client}
        payOptions={{
          metadata: {
            name: 'Buy $GURU Token',
          },
          mode: 'fund_wallet',
          prefillBuy: {
            chain: base,
            amount: '10000',
            token: {
              name: 'GURU Token',
              symbol: 'GURU',
              address: '0x0f1cFD0Bb452DB90a3bFC0848349463010419AB2',
              icon: 'https://basescan.org/token/images/gurunetwork_32.png',
            },
          },
        }}
        supportedTokens={{
          [1]: [
            {
              address: '0x525574C899A7c877a11865339e57376092168258',
              name: 'GURU Token',
              symbol: 'GURU',
              icon: 'https://etherscan.io/token/images/gurunetwork_32.png',
            },
          ],
          [8453]: [
            {
              address: '0x0f1cFD0Bb452DB90a3bFC0848349463010419AB2',
              name: 'GURU Token',
              symbol: 'GURU',
              icon: 'https://basescan.org/token/images/gurunetwork_32.png',
            },
          ],
        }}
      />
    </div>
  )
}
