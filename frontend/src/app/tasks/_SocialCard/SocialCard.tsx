import Image from 'next/image'

import clsx from 'clsx'

import { Burns, Caption, Card, Show } from '@/components/ui'

import styles from './SocialCard.module.scss'

type State = 'pending' | 'loading' | 'ready'

export type SocialCardProps = {
  title: string
  description: string
  src: string
  burns: number
  status: State
  readyMsg: string
  onClick?: () => void
}

export function SocialCard({
  title,
  description,
  src,
  burns,
  status = 'pending',
  readyMsg,
  onClick,
}: SocialCardProps) {
  const socialCardClassName = clsx(styles.container, {
    [styles[`status__${status}`]]: status,
  })
  return (
    <Card
      className={socialCardClassName}
      background={status === 'ready' ? 'dark-100' : 'dark-60'}
      onClick={onClick}>
      <div className={styles.body}>
        <div className={styles.illustration}>
          <Image
            className={styles.illustration__image}
            src={`/social/${src}.png`}
            width={40}
            height={40}
            alt="insta"
          />
          <Show if={status === 'ready'}>
            {/* <Icon iconName="ready" className={styles.icon} /> */}
          </Show>
        </div>
        <div className={styles.content}>
          <Caption className={styles.title}>{status === 'ready' ? readyMsg : title}</Caption>
          <Show if={status !== 'ready'}>
            <Caption size="xxs" className={styles.description}>
              {status === 'loading' ? 'Analyzing...' : description}
            </Caption>
          </Show>
        </div>
      </div>
      <Burns variant="numbers" size="md">
        {burns}
      </Burns>
    </Card>
  )
}
