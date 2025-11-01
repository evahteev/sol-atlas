import { FC } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'

import Caption from '@/components/ui/Caption'
import ImageEmpty from '@/images/mascot/prey.svg'

import styles from './AIChatWelcome.module.scss'

type AIChatWelcomeProps = {
  className?: string
}

const aiName = env('NEXT_PUBLIC_AI_NAME') || 'AI Guru'

export const AIChatWelcome: FC<AIChatWelcomeProps> = ({ className }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.illustration}>
        <ImageEmpty className={styles.image} />
      </div>
      <div className={styles.header}>
        <Caption variant="header" size="lg" className={styles.title}>
          <span className={styles.welcome}>
            <span className={styles.greeting}>Hi,</span> I am {aiName}!
          </span>{' '}
          I will help you simplify the difficult
        </Caption>{' '}
        <Caption variant="body" size="sm" className={styles.subtitle}>
          GuruAI is trying, but it still can be wrong.
        </Caption>
      </div>
    </div>
  )
}
