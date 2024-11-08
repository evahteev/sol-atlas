'use client'

import Image from 'next/image'
import Link from 'next/link'

// import Link from 'next/link'
import { Burns, Caption, Card } from '@/components/ui'

import styles from './Meme.module.scss'

export type MemeProps = {
  artId: string
  title: string
  rank: number
  description: string
  locked?: number
  participants?: number
  ratio?: [number, number]
  imageSrc: string
  hasFinances: boolean // generated, but voting not started
  isDraft?: boolean // draft state
  prompt?: string // prompt for draft state
}

export function Meme({
  artId,
  title,
  description,
  locked,
  participants,
  ratio,
  imageSrc,
  hasFinances = false,
  isDraft = false, // Default value set to false
  prompt, // Optional prompt for draft state
}: MemeProps) {
  return (
    <Link href={`/burn/${artId}`} className={styles.link}>
      <Card className={styles.container}>
        <div className={styles.illustration}>
          {!isDraft ? (
            <Image src={imageSrc} alt={title} fill={true} />
          ) : (
            <div className={styles.generating}>Generating...</div> // Placeholder for draft state
          )}
        </div>
        <div className={styles.body}>
          {!isDraft && (
            <div className={styles.title}>
              <Caption size="sm" className={styles.title__caption} strong={true}>
                {title}
              </Caption>
              {/*<Rank rank={rank} />*/}
            </div>
          )}
          {hasFinances && ratio ? (
            <div className={styles.stats}>
              <div className={styles.stat}>
                <Caption size="xs">Locked</Caption>
                <Burns size="sm" strong={true}>
                  {locked}
                </Burns>
              </div>
              <div className={styles.stat}>
                <Caption size="xs">Ratio</Caption>
                <div className={styles.ratio}>
                  <Caption size="sm" strong={true} className={styles.red}>
                    {ratio[0]}
                  </Caption>
                  <Caption size="sm" strong={true} className={styles.green}>
                    {ratio[1]}
                  </Caption>
                </div>
              </div>
              <div className={styles.stat}>
                <Caption size="xs">Participants</Caption>
                <Caption size="sm" strong={true} decorated="fire">
                  {participants}
                </Caption>
              </div>
            </div>
          ) : (
            <div className={styles.description}>
              <Caption size="sm">{!isDraft ? description : prompt}</Caption>
            </div>
          )}
        </div>
      </Card>
    </Link>
  )
}
