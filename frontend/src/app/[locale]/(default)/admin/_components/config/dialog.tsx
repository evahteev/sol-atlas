'use client'

import { FC, useState } from 'react'

import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'

import { PageCommunityConfigPropProps } from './prop'

import styles from './dialog.module.scss'

export type PageCommunityConfigDialogProps = {
  props?: Record<string, PageCommunityConfigPropProps>
  onClose: () => void
  onSubmit: (values: Record<string, string>) => void
}

export const PageCommunityConfigDialog: FC<PageCommunityConfigDialogProps> = ({
  props,
  onClose,
  onSubmit,
}) => {
  const [currentValues, setCurrentValue] = useState<Record<string, string>>(
    Object.fromEntries(Object.entries(props ?? {}).map(([key, data]) => [key, data.value || '']))
  )
  const handleSubmit = () => {
    onClose?.()
    onSubmit?.(currentValues)
  }

  const doChange = (key: string, val: string | number) => {
    setCurrentValue((prev) => ({ ...prev, [key]: `${val}` }))
  }

  return (
    <div className={styles.container}>
      <div className={styles.body}>
        <ul className={styles.list}>
          {Object.entries(props ?? {}).map(([name, data]) => {
            return (
              <li className={styles.item} key={name}>
                <FormField
                  caption={data.caption}
                  type={data.type}
                  defaultValue={data.value}
                  onValueChange={(val: string | number) => {
                    doChange(name, val)
                  }}
                />
              </li>
            )
          })}
        </ul>
      </div>
      <div className={styles.footer}>
        <Button variant="primary" size="lg" caption="Submit" onClick={handleSubmit} />
      </div>
    </div>
  )
}
