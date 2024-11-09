import { FC } from 'react'

import { Caption } from '@/components/ui'

import styles from './_assets/page.module.scss'

const PageBurn: FC = async () => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="header" size="xxl" decorated="fire" strong>
          Coming Soon: AI-Driven Web3 Automations in the Guru App
        </Caption>
        <p>
          Get ready to experience the future of Web3! With our upcoming AI-driven automations
          feature, you&apos;ll soon be able to set personalized alerts and automate your Web3
          activities seamlessly.
        </p>
        <p>
          No more manual monitoring—let the Guru App handle everything powered by smart automations
          that work for you. Web3 just got smarter, easier, and more efficient!
        </p>
      </div>
      <iframe className={styles.body} src="https://v2.dex.guru/flows" />
    </div>
  )
}

export default PageBurn
