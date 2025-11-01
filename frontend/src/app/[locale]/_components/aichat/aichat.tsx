'use client'

import { usePathname } from 'next/navigation'

import { FC, useCallback, useContext, useEffect, useState } from 'react'

import clsx from 'clsx'
import { useSession } from 'next-auth/react'
import { env } from 'next-runtime-env'

import { fetchAIChatProcess } from '@/actions/ai/chat'
import AIChat from '@/components/feature/AIChat'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
// import ButtonGroup from '@/components/ui/ButtonGroup'
import IconAI from '@/images/icons/aichat.svg'
// import IconEdit from '@/images/icons/auto.svg'
import IconClose from '@/images/icons/close.svg'
import { AppContext } from '@/providers/context'
// import IconTerminate from '@/images/icons/delete.svg'
// import IconUpdate from '@/images/icons/reload.svg'
import { components } from '@/services/flow/schema'

import styles from './aichat.module.scss'

const aiName = env('NEXT_PUBLIC_AI_NAME') || 'AI Guru'

// const getControlType = (task: components['schemas']['TaskSchema']) => {
//   const taskDefinitionKey = task.taskDefinitionKey?.toLocaleLowerCase() ?? ''
//   const name = task.name?.toLocaleLowerCase() ?? ''
//   for (const type of ['edit', 'update', 'terminate']) {
//     if (taskDefinitionKey.includes(type) || name.includes(type)) {
//       return type
//     }
//   }
// }

// const getControlIcon = (task: components['schemas']['TaskSchema']) => {
//   if (!task) {
//     return undefined
//   }

//   switch (getControlType(task)) {
//     case 'edit':
//       return <IconEdit />
//     case 'terminate':
//       return <IconTerminate />
//     case 'update':
//       return <IconUpdate />
//     default:
//       return undefined
//   }
// }

// const getControlVariant = (task: components['schemas']['TaskSchema']) => {
//   if (!task) {
//     return undefined
//   }

//   switch (getControlType(task)) {
//     case 'terminate':
//       return 'danger'
//     case 'update':
//       return 'prompt'
//     default:
//       return undefined
//   }
// }

type LayoutAIChatProps = {
  className?: string
}

export const LayoutAIChat: FC<LayoutAIChatProps> = ({ className }) => {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)
  const [instance, setInstance] = useState<components['schemas']['ProcessInstanceSchema'] | null>(
    null
  )
  const { data: session } = useSession()
  const {
    aiChat: { prompts, entry },
  } = useContext(AppContext)
  // const [controlTasks, setControlTasks] = useState<components['schemas']['TaskSchema'][]>([])

  const handleOpen = () => {
    setIsOpen(!isOpen)
  }

  useEffect(() => {
    if (!session?.user?.id || session?.user?.is_block === true || instance) {
      return
    }

    fetchAIChatProcess({ session }).then((process) => setInstance(process))
  }, [instance, session, session?.user?.id, session?.user?.is_block])

  const handleControlChange = useCallback(
    (controlTasks?: components['schemas']['TaskSchema'][]) => {
      if (controlTasks) {
        //
      }
      // setControlTasks(controlTasks ?? [])
    },
    []
  )

  if (
    pathname === '/' ||
    pathname.startsWith('/login') ||
    pathname.startsWith('/agents') ||
    !instance
  ) {
    return null
  }

  return (
    <div
      id="page-aichat"
      className={clsx(
        styles.container,
        { [styles.open]: isOpen, [styles.close]: !isOpen },
        className
      )}>
      <button className={styles.toggle} onClick={handleOpen}>
        <Show if={!isOpen}>
          <span className={styles.icon}>
            <IconAI className={styles.ai} />
          </span>
        </Show>
        <Show if={isOpen}>
          <IconClose className={styles.icon} />
        </Show>
      </button>

      <Show if={isOpen}>
        <div className={styles.header}>
          <Caption variant="header" size="lg" className={styles.title}>
            <span className={styles.caption} title={instance.id}>
              {aiName}
            </span>
          </Caption>

          {/* <Show if={controlTasks?.length}>
            <ButtonGroup
              className={styles.actions}
              buttons={controlTasks?.map((control) => {
                const icon = getControlIcon(control)
                const variant = getControlVariant(control)
                const variantClass = variant && styles[variant] ? styles[variant] : null
                return {
                  icon,
                  variant,
                  title: control.name,
                  className: clsx(styles.action, variantClass),
                }
              })}
            />
          </Show> */}
        </div>
        <div className={styles.body}>
          <AIChat
            className={styles.chat}
            instance={instance}
            onControlTasks={handleControlChange}
            prompts={prompts}
            entry={entry}
          />
        </div>
      </Show>
    </div>
  )
}
