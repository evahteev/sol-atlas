import { FC } from 'react'

import Message from '@/components/ui/Message'
import { useProcessInstanceTasks } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'

import { OnboardingResult } from './result'
import { OnboardingProcessVideo } from './video'

export const OnboardingProcess: FC<{
  processInstance: components['schemas']['ProcessInstanceSchema']
}> = ({ processInstance }) => {
  const { data: tasks } = useProcessInstanceTasks(processInstance.id)

  if (!processInstance) {
    return <Message type="danger">Unexpected use of process instance!</Message>
  }

  const taskVideo = tasks?.find(
    (task) => task.taskDefinitionKey === 'screen_appUseSignOnboardingVideo'
  )

  const taskClaim = tasks?.find(
    (task) => task.taskDefinitionKey === 'app_user_sign_up_init_balance_task'
  )

  if (taskVideo) {
    return <OnboardingProcessVideo task={taskVideo} />
  }

  return <OnboardingResult processInstance={processInstance} task={taskClaim} />
}
