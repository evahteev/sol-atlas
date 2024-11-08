import { FC } from 'react'

import { TaskFormCustomProps } from '@/app/tasks/_components/task/TaskForm'
import TaskFormCustomShareInvite from '@/app/tasks/_components/task/custom/shareInvite'

export const questCustomRoute: Record<string, string> = {
  generate_art_and_vote: '/generate',
  processUserSignUp: '/signup',
}

export const taskCustomComponent: Record<string, Record<string, FC<TaskFormCustomProps>>> = {
  invite_friends: {
    share_invite_link: TaskFormCustomShareInvite,
  },
}
