import { components } from '@/services/flow/schema'

import { TaskForm } from './TaskForm'

export default TaskForm

export const getTaskFormDataToObject = (
  form: HTMLFormElement,
  extra?: Record<string, string | number | boolean | null>
): Record<string, string | number | boolean | null> => {
  const formData = new FormData(form)

  return {
    ...(Object.fromEntries(
      formData.entries().filter(([key, value]) => key && !(value instanceof File))
    ) as Record<string, string | number | boolean | null>),
    ...extra,
  }
}

const getValueByType = (
  value: string | number | boolean | null,
  type: string = 'String'
): string | number | boolean | null => {
  switch (type) {
    case 'Boolean':
      return value === true || value === 'true' || value === 'on'
    case 'Integer':
    case 'Long':
    case 'Double':
      return Number(value || 0)
    case 'Date': {
      const date = new Date(`${value}` || Date.now())
      return date.toISOString()
    }
    default:
      return value ?? null
  }

  return null
}

const getVariableData = (
  value: string | number | boolean | null = null,
  initial?: components['schemas']['VariableValueSchema']
): {
  value: string | number | boolean | null
  type?: string
  valueInfo?: Record<string, never> | null
} => {
  if (!initial?.type) {
    return { value: value ?? null }
  }

  return {
    value: getValueByType(
      (value ?? initial.value) as string | number | boolean | null,
      initial.type
    ),
  }
}

export const getVariablesFromObject = (
  varObject: Record<string, string | number | boolean | null>,
  initial?: Record<string, components['schemas']['VariableValueSchema']>
) => {
  // Filter out empty values first
  const filteredVarObject = Object.fromEntries(
    Object.entries(varObject).filter(([key, value]) => {
      // Skip empty keys and empty values
      if (!key || value === null || value === '' || value === undefined) {
        return false
      }
      return true
    })
  )

  const varNames = [...new Set([...Object.keys(initial ?? {}), ...Object.keys(filteredVarObject)])]
  const variables: Record<string, { value: string | number | boolean | null }> = {}

  varNames.forEach((name) => {
    // Only process if the name exists in filteredVarObject or initial
    if (filteredVarObject[name] || initial?.[name]) {
      variables[name] = getVariableData(filteredVarObject[name], initial?.[name])
    }
  })

  return variables
}
