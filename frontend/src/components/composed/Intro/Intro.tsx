import dynamic from 'next/dynamic'

import { FC } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'

import Loader from '@/components/atoms/Loader'
import Show from '@/components/ui/Show'

import styles from './Intro.module.scss'

type IntroProps = {
  className?: string
  isLoading?: boolean
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ImageBrand = dynamic<any>(() => import(`skins/theme/assets/images/brand/intro.svg`))

export const Intro: FC<IntroProps> = ({ className, isLoading }) => {
  return (
    <div
      className={clsx(styles.container, { [styles.loading]: isLoading }, className)}
      style={{ background: env('NEXT_PUBLIC_APP_INTRO_BG') }}>
      <div className={styles.header}>
        <div className={styles.illustration}>
          <ImageBrand className={styles.brand} />
        </div>
      </div>

      <div className={styles.body}>
        <Show if={env('NEXT_PUBLIC_APP_INTRO_TITLE')}>
          <h1 className={styles.title}>{env('NEXT_PUBLIC_APP_INTRO_TITLE')}</h1>
        </Show>
        <span className={styles.subtitle}>
          {env('NEXT_PUBLIC_APP_INTRO_SUBTITLE') || env('NEXT_PUBLIC_APP_INTRO')}
        </span>
        <Loader className={styles.loader} />
      </div>

      <Show if={process.env.NEXT_PUBLIC_GIT_COMMIT}>
        <div className={styles.footer}>
          <span className={styles.version}>Version {process.env.NEXT_PUBLIC_GIT_COMMIT}</span>
        </div>
      </Show>
    </div>
  )
}
