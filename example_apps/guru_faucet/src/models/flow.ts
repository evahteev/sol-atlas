import { components } from '@/services/flow/schema'

export type FlowModel = components['schemas']['FlowRest']

export type FlowInstanceModel = components['schemas']['ProcessInstanceSchema']

export type FlowInstanceWithVariables = FlowInstanceModel & {
  variables: (components['schemas']['VariableValueSchema'] & { name: string })[]
}
