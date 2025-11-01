import { FC, ReactNode, useEffect, useState } from 'react'

import clsx from 'clsx'

import FormField from '@/components/composed/FormField'

import styles from './filter.module.scss'

type TokensExplorerTableFilterFieldValueProps = {
  value?: string
  label: ReactNode
  icon?: ReactNode
}

type TokensExplorerTableFilterFieldProps = {
  caption?: ReactNode
  options: TokensExplorerTableFilterFieldValueProps[]
}

type TokensExplorerTableFilterProps = {
  fields: Record<string, TokensExplorerTableFilterFieldProps>
  className?: string
  onChange?: (values: Record<string, string>) => void
  defaultValue?: TokensExplorerTableFilterValueProps
  value?: TokensExplorerTableFilterValueProps
}

type TokensExplorerTableFilterValueProps = Record<string, string>

export const TokensExplorerTableFilter: FC<TokensExplorerTableFilterProps> = ({
  className,
  fields,
  onChange,
  defaultValue,
  value,
}) => {
  const [currentValue, setCurrentValue] = useState<Record<string, string>>(
    Object.entries(fields).reduce((acc, [key, field]) => {
      acc[key] = value?.[key] ?? defaultValue?.[key] ?? field.options[0].value ?? ''
      return acc
    }, {} as TokensExplorerTableFilterValueProps)
  )

  useEffect(() => {
    if (value) {
      setCurrentValue(value)
    }
  }, [value])

  useEffect(() => {
    onChange?.(currentValue)
  }, [currentValue, onChange])

  return (
    <div className={clsx(styles.container, className)}>
      <ul className={styles.list}>
        {Object.entries(fields).map(([key, field]) => {
          return (
            <li className={styles.item} key={key}>
              <FormField
                type="select"
                options={field.options}
                value={currentValue[key]}
                onChange={(e) => {
                  setCurrentValue((prev) => ({ ...prev, [key]: e.target.value ?? '' }))
                }}
              />
            </li>
          )
        })}
      </ul>
    </div>
  )
}
