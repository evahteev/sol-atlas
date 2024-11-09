'use client'

import { FC } from 'react'

import FormField from '@/components/composed/FormField'

import { useQueryResponse } from '../hooks'

export const WarehouseDashboardParamQuery: FC<{
  className?: string
  caption: string
  name: string
  value: string
  queryId: number
  onValueChange: (value: string | null) => void
}> = ({ queryId, onValueChange, ...props }) => {
  const { isFetching, result } = useQueryResponse({ queryId })

  const options = result?.data.rows.map((item) => ({ value: `${item.value}`, label: item.name }))

  return (
    <FormField
      type="select"
      disabled={isFetching}
      {...props}
      options={options ?? [{ value: props.value, label: props.value }]}
      onValueChange={(target) => {
        onValueChange(target?.value ?? null)
      }}
    />
  )
}
