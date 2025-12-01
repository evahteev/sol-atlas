'use client'

import { CSSProperties, FC } from 'react'

import clsx from 'clsx'

import { Session } from '@/lib/session'

import { TaskFormVariable } from '../types'
import { TaskFormDeployedField } from './TaskFormDeployedField'
import { TaskFormDeployedComponent } from './types'

import styles from '../TaskForm.module.scss'

export const TaskFormDeployedLayout: FC<{
  components?: TaskFormDeployedComponent[]
  variables?: Record<string, TaskFormVariable>
  className?: string
  session?: Session | null
  onFormComplete?: (params?: {
    business_key?: string
    variables: Record<string, TaskFormVariable>
  }) => void
  style?: CSSProperties
}> = ({ components, variables, className, session, onFormComplete, style }) => {
  if (!components?.length) {
    return null
  }

  const rows: Record<string, TaskFormDeployedComponent[]> = (components ?? []).reduce(
    (acc, field) => {
      const row = field.layout?.row || 'default'
      if (!acc[row]) {
        acc[row] = []
      }
      acc[row].push(field)
      return acc
    },
    {} as Record<string, TaskFormDeployedComponent[]>
  )

  return (
    <div style={style} className={clsx(styles.layout, className)}>
      {Object.entries(rows).map(([rowId, rowFields]) => {
        const fieldsColumns = rowFields.map((field) => field.layout?.columns ?? null)
        const columnsFixed = fieldsColumns
          .filter((column) => column !== null)
          .reduce((sum, cols) => sum + (cols ?? 0), 0)
        const dynamicFields = fieldsColumns.filter((cols) => cols === null)
        const remaining = 16 - columnsFixed
        const defaultSpan = Math.floor(remaining / dynamicFields.length)

        return (
          <div key={rowId} className={styles.layoutRow}>
            {rowFields.map((field) => {
              return (
                <div
                  key={field.id}
                  className={clsx(styles.layoutField, styles[`layoutField-${field.type}`])}
                  style={{ '--_cols': field.layout?.columns || defaultSpan } as CSSProperties}>
                  <TaskFormDeployedField
                    field={field}
                    session={session}
                    variables={variables}
                    onFormComplete={onFormComplete}
                  />
                </div>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
