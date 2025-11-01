'use client'

import { FC, PropsWithChildren, ReactNode, useState } from 'react'

import clsx from 'clsx'

import ImageFallback from '@/components/atoms/ImageFallback'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Dialog from '@/components/ui/Dialog'
import Show from '@/components/ui/Show'
import IconEdit from '@/images/icons/edit.svg'

import { PageCommunityConfigDialog } from './dialog'
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
  const [isOpen, setIsOpen] = useState(false)
  const hasProps = !!Object.keys(props ?? {}).length

  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  const handleSubmit = (values: Record<string, string>) => {
    console.log(values)
  }

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

          <Show if={hasProps}>
            <Button
              icon={<IconEdit className={styles.icon} />}
              caption="Edit"
              size="sm"
              className={styles.edit}
              onClick={handleOpen}
            />
          </Show>
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

      <Dialog type="dialog" caption={caption} isOpen={isOpen} onClose={handleClose}>
        <PageCommunityConfigDialog props={props} onClose={handleClose} onSubmit={handleSubmit} />
      </Dialog>
    </>
  )
}
