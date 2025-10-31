import Image from 'next/image'

import { FC, useEffect, useState } from 'react'

import clsx from 'clsx'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { useArtsByCollection } from '@/services/flow/hooks/flow'

import styles from './collection.module.scss'

type TaskFormFieldCollectionProps = {
  className?: string
  id: string
  name: string
  title?: string | null
}

export const TaskFormFieldCollection: FC<TaskFormFieldCollectionProps> = ({
  className,
  id,
  name,
  title,
}) => {
  const { data, isLoading } = useArtsByCollection(id)
  const [currentId, setCurrentId] = useState<string | null>(null)

  useEffect(() => {
    setCurrentId((prevId) => {
      return data?.find((item) => (prevId ? item.id === prevId : null))?.id ?? data?.[0].id ?? null
    })
  }, [data])

  return (
    <div className={clsx(styles.container, className)}>
      <Show if={title}>
        <div className={styles.header}>
          <Caption variant="body" size="md" className={styles.title}>
            {title}
          </Caption>
        </div>
      </Show>
      <div className={styles.body}>
        <ul className={styles.list}>
          <Show if={data?.length}>
            {data?.map((item) => {
              return (
                <li key={item.id} className={styles.item}>
                  <label className={styles.entry}>
                    <input
                      type="radio"
                      name={name}
                      className={styles.control}
                      checked={item.id === currentId}
                      value={item.id}
                      onChange={() => {
                        setCurrentId(item.id)
                      }}
                    />
                    <Show if={item.img_picture}>
                      <Image
                        src={item.img_picture ?? ''}
                        width={88}
                        height={88}
                        alt={item.description ?? ''}
                        className={styles.image}
                      />
                    </Show>
                    <Show if={!item.img_picture}>
                      <span className={clsx(styles.image, styles.loading)} />
                    </Show>
                  </label>
                </li>
              )
            })}
          </Show>

          <Show if={!data?.length && isLoading}>
            {Array.from(Array(10))?.map((_, idx) => {
              return (
                <li key={idx} className={styles.item}>
                  <span className={styles.entry}>
                    <span className={clsx(styles.image, styles.loading)}></span>
                  </span>
                </li>
              )
            })}
          </Show>
        </ul>
      </div>
    </div>
  )
}
