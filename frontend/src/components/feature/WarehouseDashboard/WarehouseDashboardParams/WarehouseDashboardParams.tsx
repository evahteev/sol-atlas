'use client'

import { FC, useEffect, useState } from 'react'

import clsx from 'clsx'
import { omit } from 'lodash'
import { format } from 'url'

import { TWarehouseDashboard, TWarehouseQueryParam } from '@/actions/warehouse/types'
import { getDateRangeToString } from '@/actions/warehouse/utils'
import FormField from '@/components/composed/FormField'
import { Button } from '@/components/ui'
import { isTypeObject } from '@/utils'
import { DYNAMIC_DATE_PREFIX, DYNAMIC_DATE_RANGES, getShortDate } from '@/utils/dates'

import { WarehouseDashboardParamQuery } from './WarehouseDashboardParamQuery'

import styles from './WarehouseDashboardParams.module.scss'

export const WarehouseDashboardParams: FC<{
  className: string
  dashboard: TWarehouseDashboard
  params?: Record<string, TWarehouseQueryParam>
  readOnlyParams?: string[]
}> = ({ params, readOnlyParams, className }) => {
  const [currentParams, setCurrentParams] = useState(params ?? {})
  const [currentHref, setCurrentHref] = useState('')

  useEffect(() => {
    const query: Record<string, string> = Object.fromEntries(
      new URLSearchParams(window.location.search).entries()
    )
    Object.values(currentParams).forEach(({ type, name, value }) => {
      query[name] =
        `${(['date-range', 'datetime-range', 'datetime-range-with-seconds'].includes(type) ? getDateRangeToString(value) : value) || ''}`
    })

    setCurrentHref(format({ query }) || '?')
  }, [currentParams])

  const editableParams: Record<string, TWarehouseQueryParam> = omit(
    currentParams,
    readOnlyParams ?? []
  )

  if (!Object.keys(editableParams).length) {
    return null
  }

  const isChanged =
    Object.values(currentParams)
      .map((param) => params?.[param.name].value === param.value)
      .filter((item) => !item).length > 0

  return (
    <div className={clsx(styles.container, className)}>
      {Object.values(editableParams)
        .filter((item) => item.level === 'dashboard-level')
        .map((prop) => {
          const { name, title, type, value } = prop
          const isDateRangeObj =
            typeof value !== 'string' && isTypeObject(value) && !!value?.start && !!value?.end

          const commonProps = {
            id: `${name}-${type}`,
            className,
            caption: title,
            name,
            value: isDateRangeObj ? '' : `${value || ''}`,
          }

          if (['date-range', 'datetime-range', 'datetime-range-with-seconds'].includes(type)) {
            const valStr = isDateRangeObj
              ? `${getShortDate(value.start ?? '')} – ${getShortDate(value.end ?? '')}`
              : `${value ?? ''}`

            const options = Object.entries(DYNAMIC_DATE_RANGES).map(([key, option]) => ({
              value: `${DYNAMIC_DATE_PREFIX}${key}`,
              label: option.name,
            }))

            return (
              <FormField
                key={name}
                {...commonProps}
                value={valStr}
                type="select"
                placeholder={
                  isDateRangeObj
                    ? `${getShortDate(value.start ?? '')} - ${getShortDate(value.end ?? '')}`
                    : undefined
                }
                options={options}
                onValueChange={(target) => {
                  const value = target?.value
                  setCurrentParams((prev) => ({
                    ...prev,
                    [name]: { ...prev[name], value: value || null },
                  }))
                }}
              />
            )
          }

          if (prop.type === 'query' && prop.queryId) {
            return (
              <WarehouseDashboardParamQuery
                key={name}
                queryId={prop.queryId}
                {...commonProps}
                onValueChange={(value) => {
                  setCurrentParams((prev) => ({
                    ...prev,
                    [name]: { ...prev[name], value: value || null },
                  }))
                }}
              />
            )
          }

          return (
            <FormField
              key={name}
              {...commonProps}
              onValueChange={(target) => {
                const value = target?.value
                setCurrentParams((prev) => ({
                  ...prev,
                  [name]: { ...prev[name], value: value || null },
                }))
              }}
            />
          )
        })}

      <Button
        scroll={false}
        caption="Apply Changes"
        isDisabled={!isChanged}
        variant="primary"
        size="xl"
        href={isChanged ? currentHref : '?'}
      />
    </div>
  )
}
