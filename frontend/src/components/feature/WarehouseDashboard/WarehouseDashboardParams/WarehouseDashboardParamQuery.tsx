'use client'

import { FC } from 'react'

import FormField from '@/components/composed/FormField'

import { useQueryResponse } from '../../../../hooks/warehouse/useQueryResponse'

export const WarehouseDashboardParamQuery: FC<{
  className?: string
  caption: string
  name: string
  value: string
  queryId: number
  onValueChange: (value: string | null) => void
}> = ({ queryId, onValueChange, ...props }) => {
  const { isFetching, result } = useQueryResponse({ queryId, maxAge: 60 })

  const options = result?.data.rows.map((item) => {
    const defaultItemName = Object.values(item)[0]
    return { value: `${item.value ?? defaultItemName}`, label: `${item.name ?? defaultItemName}` }
  })

  return (
    <FormField
      type="select"
      disabled={isFetching}
      {...props}
      options={options ?? [{ value: `${props.value}`, label: `${props.value}` }]}
      onValueChange={(value) => {
        onValueChange(value ?? null)
      }}
    />
  )
}
