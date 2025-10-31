'use client'

import { FC, PropsWithChildren, ReactNode } from 'react'

import clsx from 'clsx'

import ImageFallback from '@/components/atoms/ImageFallback'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Show from '@/components/ui/Show'

import { PageCommunityConfigProp, PageCommunityConfigPropProps } from './prop'

import styles from './config.module.scss'

type PageCommunityConfigProps = PropsWithChildren<{
  className?: string
  caption: ReactNode
  description?: ReactNode
  props?: Record<string, PageCommunityConfigPropProps>
  imageURL?: string
}>

export const PageCommunityConfig: FC<PageCommunityConfigProps> = ({
  className,
  caption,
  description,
  props,
  imageURL,
  children,
}) => {
  const hasProps = !!Object.keys(props ?? {}).length

  return (
    <>
      <Card className={clsx(styles.container, className)}>
        <Show if={imageURL}>
          <ImageFallback
            src={imageURL}
            fallback={<span className={styles.illustration} />}
            className={styles.illustration}
          />
        </Show>

        <span className={styles.header}>
          <Caption variant={imageURL ? 'header' : 'body'} size="lg" className={styles.title}>
            {caption}
          </Caption>

          <div className={styles.description}>{description}</div>
        </span>

        <div className={styles.body}>
          <Show if={hasProps}>
            <div className={styles.props}>
              <ul className={styles.list}>
                {Object.entries(props ?? {}).map(([name, data]) => {
                  return (
                    <li className={styles.item} key={name}>
                      <PageCommunityConfigProp
                        caption={data.caption}
                        value={data.value}
                        icon={data.icon}
                        type={data.type}
                        className={styles.prop}
                      />
                    </li>
                  )
                })}
              </ul>
            </div>
          </Show>
          {children}
        </div>
      </Card>
    </>
  )
}
