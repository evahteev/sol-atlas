import get from 'lodash/get'

import { TaskFormVariable } from '@/components/composed/TaskForm/types'

export const getShortAddress = (address?: string, count = 4): string => {
  const charCount = Math.max(count, 4)

  const regexp = new RegExp(`(0x)([0-9a-f]{${charCount - 1}})(.+)([0-9a-f]{${charCount}})`, 'i')

  const result = `${address}`.replace(regexp, '$1$2…$4')
  return result
}

export const pluralize = (
  count: number,
  forms: { one: string; zero?: string; two?: string; few?: string; many?: string; other?: string },
  locale = 'en'
): string => {
  const pr = new Intl.PluralRules(locale)
  const category = pr.select(count)
  return forms[category] ?? forms.other ?? forms.one
}

export const replaceTemplateVariables = (
  text?: string,
  variables: Record<string, TaskFormVariable> = {}
): string => {
  if (!text) {
    return ''
  }

  let result = text

  const varsEntries = text.matchAll(/\{\{(.+?)\}\}/g)

  for (const match of varsEntries) {
    const groupSelection = match[1].trim()

    const [variableName, fallbackValiue] = groupSelection
      .split('||')
      .map((x) => x.trim().replace(/'/g, ''))

    let value = match[0]

    const variableValue = variables?.[variableName]?.value || fallbackValiue

    try {
      if (variableName.includes('.')) {
        const [key, ...path] = variableName.split('.')
        const variableValue = variables?.[key]?.value

        value = get(JSON.parse(`${variableValue}`), path.join('.'))
      } else {
        value = `${variableValue}`
      }
    } catch (e) {
      console.error(e)
      value = fallbackValiue || value
    }

    result = result.replace(match[0], value)
  }

  return result
}

export const hashOfString = (s: string): number =>
  s.split('').reduce((a, b) => ((a << 5) - a + b.charCodeAt(0)) | 0, 0)
