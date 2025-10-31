'use client'

import { useRouter } from 'next/navigation'

import {
  ChangeEventHandler,
  FC,
  FormEventHandler,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import clsx from 'clsx'
import { useInView } from 'react-intersection-observer'
import { toast } from 'react-toastify'

import Loader from '@/components/atoms/Loader'
import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import {
  HistoricProcessInstanceEventEntity,
  useProcessInstanceWithWS,
} from '@/hooks/flow/useProcessInstanceWithWS'
import { useDidMount } from '@/hooks/useDidMount'
import IconSend from '@/images/icons/arrow-up.svg'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

import { AIChatMessage } from './AIChatMessage'
import { AIChatWelcome } from './AIChatWelcome'

import styles from './AIChat.module.scss'

export type AIChatPrompt = {
  label: string
  value: string
}

type AIChatProps = {
  className?: string
  instance: components['schemas']['ProcessInstanceSchema']
  prompts?: AIChatPrompt[] | null
  entry?: { type: string; id: string } | null
  tasks?: components['schemas']['TaskSchema'][] | null
  onControlTasks?: (tasks?: components['schemas']['TaskSchema'][]) => void
}

export const AIChatLegacy: FC<AIChatProps> = ({
  className,
  instance,
  prompts,
  entry,
  // tasks: initialTasks,
  onControlTasks,
}) => {
  const refInput = useRef<HTMLTextAreaElement>(null)
  const [isBlocked, setIsBlocked] = useState(true)
  const [isEmpty, setIsEmpty] = useState(true)
  const [isShowScroll, setIsShowScroll] = useState(false)

  const [chatHistory, setChatHistory] = useState<components['schemas']['TaskSchema'][]>([]) // TODO: check if this solution really works
  const [refLast, isInEnd, elLast] = useInView()

  const isMounted = useDidMount()

  const scrollToEnd = useCallback(
    (behavior: 'smooth' | 'instant' = 'smooth') => {
      elLast?.target?.scrollIntoView({ behavior })
    },
    [elLast?.target]
  )
  const router = useRouter()
  const onProcessInstanceEnd = useCallback(
    (event: HistoricProcessInstanceEventEntity) => {
      console.log(`process instance has ended`, event)
      router.push('/agents')
    },
    [router]
  )
  const { tasks, currentActivity } = useProcessInstanceWithWS({
    processInstanceId: instance.id,
    schema: {
      processInstanceBusinessKey: instance.businessKey,
    },
    // initialData: { tasks: initialTasks }, TODO: causes chat glitching
    onProcessInstanceEnd,
    query: {
      refetchInterval: 2 * 60 * 1000,
    },
  })

  useEffect(() => {
    const input = refInput.current

    const handleKeyEnter = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !isEmpty) {
        e.preventDefault()
        handleSend()
      }
    }

    input?.addEventListener('keypress', handleKeyEnter)

    return () => {
      input?.removeEventListener('keypress', handleKeyEnter)
    }
  })

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = (e) => {
    setIsEmpty(!e.target.value.length)
  }

  const formReplyTask = tasks.findLast(
    (task) => task.taskDefinitionKey === 'form_reply' && task.state === 'ACTIVE'
  )

  useEffect(() => {
    setIsBlocked(isEmpty || !formReplyTask)
  }, [formReplyTask, isEmpty])

  const handleSubmit: FormEventHandler<HTMLFormElement> = useCallback(
    (e) => {
      if (isBlocked) {
        e.preventDefault()
      }
    },
    [isBlocked]
  )

  const handleSend = useCallback(async () => {
    if (!formReplyTask) {
      toast.error(
        'Please wait until new reply slot will be available. Try to resend your message in a minute 🙌'
      )
      console.error('Reply task is unavailable')
      return
    }
    if (!refInput?.current?.value) {
      throw new Error('Reply cannot be empty')
    }

    setIsBlocked(true)

    FlowClientObject.engine.task
      .complete(formReplyTask.id, {
        form_reply: {
          type: 'String',
          value: refInput.current.value,
        },
        form_replyMessageType: {
          type: 'String',
          value: 'DM_UI',
        },
        entry_type: {
          type: 'String',
          value: entry?.type || '',
        },
        entry_id: {
          type: 'String',
          value: entry?.id || '',
        },
      })
      .then(() => {
        //
      })
      .catch((e) => {
        console.error(e)
        toast.error('Error sending request')
      })

    setIsEmpty(true)

    if (refInput.current) {
      refInput.current.value = ''
      refInput.current.focus()
    }
  }, [entry, formReplyTask])

  const isChatEntry = (task: components['schemas']['TaskSchema']) =>
    ['human_reply'].includes(task.taskDefinitionKey ?? '') ||
    task.taskDefinitionKey?.startsWith('llm_reply')
  const isControlEntry = (task: components['schemas']['TaskSchema']) =>
    task.taskDefinitionKey?.startsWith('control_')

  const chatHistoryTasks = tasks.filter(isChatEntry)
  const controlTasks = tasks.filter(isControlEntry)

  useEffect(() => {
    onControlTasks?.(controlTasks ?? [])
  }, [controlTasks, onControlTasks])

  useEffect(() => {
    if (JSON.stringify(chatHistoryTasks) === JSON.stringify(chatHistory)) {
      return
    }

    setChatHistory((prevHistory) => {
      if (prevHistory.length !== chatHistoryTasks.length) {
        return chatHistoryTasks
      }
      return prevHistory
    })
  }, [chatHistory, chatHistoryTasks])

  useEffect(() => {
    if (isMounted && chatHistory.length) {
      scrollToEnd('instant')
    }
  }, [chatHistory.length, isMounted, scrollToEnd])

  useEffect(() => {
    setIsShowScroll(!isInEnd)
  }, [isInEnd])

  useEffect(() => {
    if (isInEnd) {
      scrollToEnd()
    }
  }, [chatHistory, isInEnd, scrollToEnd])

  const handleFocus = () => {
    scrollToEnd()
  }

  const handleScroll = () => {
    scrollToEnd()
  }

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.body}>
        <Show if={!chatHistory?.length}>
          <AIChatWelcome className={styles.welcome} />
        </Show>

        <Show if={chatHistory?.length}>
          <ul className={styles.list}>
            {chatHistory.map((entry) => (
              <li className={styles.item} key={entry.id}>
                <AIChatMessage entry={entry} className={styles.message} />
              </li>
            ))}
          </ul>

          <span className={styles.service}>{currentActivity || <>&nbsp;</>}</span>

          <Button
            size="xxs"
            caption="Scroll to the bottom"
            className={clsx(styles.scroll, { [styles.show]: isShowScroll })}
            onClick={handleScroll}
          />
        </Show>
        <div ref={refLast} />
      </div>

      <form
        className={clsx(styles.footer, {
          [styles.empty]: isBlocked,
          [styles.warming]: !chatHistory.length && !formReplyTask,
        })}
        action={handleSend}
        onSubmit={handleSubmit}>
        <Show if={prompts?.length}>
          <div className={styles.prompts}>
            {prompts?.map((prompt, idx) => (
              <Button
                key={idx}
                caption={prompt.label}
                className={styles.prompt}
                isOutline
                size="xs"
                disabled={!refInput.current}
                onClick={() => {
                  if (!refInput.current) {
                    return
                  }

                  refInput.current.value = prompt.value
                  setIsEmpty(false)
                  handleSend()
                }}
              />
            ))}
          </div>
        </Show>
        <FormField
          type="textarea"
          className={clsx(styles.input, { [styles.blocked]: !formReplyTask })}
          autoFocus={true}
          autoComplete="off"
          placeholder="How can I help you?"
          ref={refInput}
          onChange={handleChange}
          onFocus={handleFocus}
          name="message"
          indicator={!formReplyTask ? <Loader className={styles.indicator} /> : null}
        />
        <button type="submit" className={styles.submit} disabled={isBlocked}>
          <IconSend className={styles.icon} />
        </button>
      </form>

      <Show if={!chatHistory.length}>
        <div className={clsx(styles.footer, styles.loading)}>
          <Loader className={styles.loader} />
        </div>
      </Show>
    </div>
  )
}
