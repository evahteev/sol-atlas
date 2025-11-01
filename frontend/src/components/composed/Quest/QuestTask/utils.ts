/**
 * Groups Camunda task form variables by their prefix type.
 * @param variables - Camunda task form variables
 * @returns An object grouping the variables by their prefix type
 */
export const groupTaskFormVariables = (
  variables?: Record<
    string,
    {
      value: unknown
      type?: string | null
      label?: string | null
    }
  >
) => {
  if (!variables) return null

  const result = Object.entries(variables).reduce(
    (acc, [varName, varData]) => {
      const section = getTypeByVarPrefix(varName)
      if (!acc[section]) {
        acc[section] = {}
      }
      acc[section][varName ?? 'unknown'] = varData

      return acc
    },
    {} as Record<
      string,
      Record<
        string,
        {
          value: unknown
          type?: string | null
          label?: string | null
        }
      >
    >
  )
  return result
}

// Helper function to determine the type by variable prefix
const getTypeByVarPrefix = (name: string) => {
  const prefix = name.match(/^([a-zA-Z]+)_(.*)/)?.[1]
  return prefix?.replace(/(text|link)/, 'message') ?? 'default'
}

export default groupTaskFormVariables
