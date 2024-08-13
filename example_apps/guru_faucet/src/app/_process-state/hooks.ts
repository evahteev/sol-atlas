import { useProcessInstanceTasks, useProcessInstances } from '@/services/flow/hooks'

export type VariableHistoryEvent = {
  id: string | null // null
  rootProcessInstanceId: string // '431c86aa-2e7c-11ef-8ee2-a242164bf202'
  processInstanceId: string // '431d22f7-2e7c-11ef-8ee2-a242164bf202'
  executionId: string // '431d22f7-2e7c-11ef-8ee2-a242164bf202'
  processDefinitionId: string // 'generate_season_artwork:20:4223f777-289b-11ef-aa44-9a90e89572fd'
  processDefinitionKey: string // 'generate_season_artwork'
  processDefinitionName: string // null
  processDefinitionVersion: string // null
  caseInstanceId: string // null
  caseExecutionId: string // null
  caseDefinitionId: string // null
  caseDefinitionKey: string // null
  caseDefinitionName: string // null
  eventType: string // 'create'
  sequenceCounter: number // 1
  removalTime: string // null
  activityInstanceId: string // 'comfy_season_blend:431d4a11-2e7c-11ef-8ee2-a242164bf202'
  taskId: string // null
  timestamp: number // 1718829706967
  tenantId: string // null
  userOperationId: string // '58a2c81f-2e7c-11ef-8ee2-a242164bf202'
  revision: number // 0
  variableName: string // 'gen_token_name'
  variableInstanceId: string // '58a2ef36-2e7c-11ef-8ee2-a242164bf202'
  scopeActivityInstanceId: string // '431d22f7-2e7c-11ef-8ee2-a242164bf202'
  serializerName: string // 'string'
  longValue: number // null
  doubleValue: number // null
  textValue: string // 'Space Exploration'
  textValue2: string // null
  byteValue: string // null
  byteArrayId: string // null
  initial: boolean // false
  persistentState: string // 'org.camunda.bpm.engine.impl.history.event.HistoryEvent'
}
export type UserTaskHistoryEvent = {
  id: string // '58a4eb26-2e7c-11ef-8ee2-a242164bf202'
  rootProcessInstanceId: string // '431c86aa-2e7c-11ef-8ee2-a242164bf202'
  processInstanceId: string // '431c86aa-2e7c-11ef-8ee2-a242164bf202'
  executionId: string // '58a4c413-2e7c-11ef-8ee2-a242164bf202'
  processDefinitionId: string // '426853a0-289b-11ef-aa44-9a90e89572fd'
  processDefinitionKey: string // 'generate_invite_season_2_start_form'
  processDefinitionName: string // null
  processDefinitionVersion: string // null
  caseInstanceId: string //  null
  caseExecutionId: string // null
  caseDefinitionId: string // null
  caseDefinitionKey: string //  null
  caseDefinitionName: string // null
  eventType: string // 'update'
  sequenceCounter: 0
  removalTime: string // null
  durationInMillis: string // null
  startTime: 1718829706981
  endTime: null
  taskId: string // '58a4eb26-2e7c-11ef-8ee2-a242164bf202'
  assignee: string //  '0f8ea73d'
  owner: null
  name: string // 'Share socials and be able to mint'
  description: null
  dueDate: null
  followUpDate: null
  priority: 50
  parentTaskId: null
  deleteReason: null
  taskDefinitionKey: string //  'review_modal_share_socials'
  activityInstanceId: string // 'review_modal_share_socials:58a4c415-2e7c-11ef-8ee2-a242164bf202'
  tenantId: null
  durationRaw: null
  persistentState: string // 'org.camunda.bpm.engine.impl.history.event.HistoryEvent'
}

export const useSeasonPassInvite = (processDefinitionKey: string) => {
  const { data: processInstances, isFetched: isFetchedProcessInstance } =
    useProcessInstances(processDefinitionKey)

  const processInstance = processInstances?.[0]

  const {
    data: tasks,
    error,
    isFetched: isFetchedProcessInstanceTasks,
  } = useProcessInstanceTasks(processInstance?.id)
  return {
    processInstance,
    tasks: error ? undefined : tasks,
    isFetchedProcessInstance,
    isFetched: isFetchedProcessInstance && isFetchedProcessInstanceTasks,
  }
}
