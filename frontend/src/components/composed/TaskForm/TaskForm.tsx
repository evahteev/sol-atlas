'use client'

import { FC, useEffect, useState } from 'react'

import Loader from '@/components/atoms/Loader'
import { useSession } from '@/hooks/useAuth.compat'
import { useTasks } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'

import RequireLogin from '../RequireLogin'
import StateMessage from '../StateMessage'
import TaskFormDeployed from './TaskFormDeployed'
import TaskFormFromVars from './TaskFormFromVars'
import { TaskFormProps } from './types'

import styles from './TaskForm.module.scss'

export const TaskForm: FC<TaskFormProps> = (props) => {
  const { data: session } = useSession()
  const { taskId, startForm = 'none' } = props

  const isCamundaStartForm = !!startForm && !['embedded', 'unknown', 'none'].includes(startForm)
  const isStartForm = startForm !== 'none'

  const [task, setTask] = useState<components['schemas']['TaskSchema']>()

  const {
    data: tasks,
    isError,
    isFetched,
  } = useTasks({
    schema: { taskId },
    query: {
      enabled: !isStartForm && task?.id !== props.taskId,

      refetchInterval: false,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
      refetchOnMount: false,
    },
    session,
  })

  useEffect(() => {
    setTask(tasks?.[0])
  }, [tasks, props.taskId])

  const isDeployedForm = isCamundaStartForm || !!task?.camundaFormRef?.key

  if (startForm === 'unknown') {
    return <StateMessage type="danger" caption="Error while processing start form" />
  }

  if (!isStartForm && task?.id !== props.taskId) {
    return <Loader className={styles.loader} />
  }

  if (!isStartForm && ((!task && isFetched) || isError)) {
    return <StateMessage type="danger" caption="Error while loading task" />
  }

  if (isDeployedForm) {
    return (
      <TaskFormDeployed
        {...props}
        instanceId={task?.processInstanceId}
        session={session}
        isStartForm={isCamundaStartForm && !task?.processInstanceId}
      />
    )
  }

  return (
    <RequireLogin>
      <TaskFormFromVars task={task} {...props} session={session} />
    </RequireLogin>
  )
}
