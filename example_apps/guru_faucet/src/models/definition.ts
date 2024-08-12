import { components } from '@/services/flow/schema'

export type DefinitionModel = components['schemas']['ProcessDefinitionSchema']

export type DefinitionInstanceModel = components['schemas']['ProcessInstanceSchema']

export type DefinitionInstanceWithVariables = DefinitionInstanceModel & {
  variables: (components['schemas']['VariableValueSchema'] & { name: string })[]
}
