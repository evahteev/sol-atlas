import { FC } from 'react'

import { TaskFormProps } from '@/components/composed/TaskForm/types'

import TaskFormCustomShareInvite from './custom/shareInvite'
import TaskFormCustomSwapToken from './custom/swapToken'

export const questCustomRoute: Record<string, string> = {
  generate_art_and_vote: '/generate',
  // processUserSignUp: '/signup',
}

type TaskFromStartProps = TaskFormProps & { isStartForm?: boolean }

export const taskCustomComponent: Record<
  string,
  { start?: FC<TaskFromStartProps>; tasks?: Record<string, FC<TaskFromStartProps>> }
> = {
  invite_friends: {
    tasks: {
      share_invite_link: TaskFormCustomShareInvite,
    },
  },
  swap_tokens: {
    start: TaskFormCustomSwapToken,
  },
}
