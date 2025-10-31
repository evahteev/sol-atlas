'use client'

import {
  ChangeEventHandler,
  FC,
  FormEventHandler,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import { CopilotKit, useCopilotChat } from '@copilotkit/react-core'
import { MessageRole, TextMessage } from '@copilotkit/runtime-client-gql'
import clsx from 'clsx'
import { useInView } from 'react-intersection-observer'

import Loader from '@/components/atoms/Loader'
import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { useDidMount } from '@/hooks/useDidMount'
import IconSend from '@/images/icons/arrow-up.svg'

import { AIChatPrompt } from './AIChat'
import { AIChatMessage } from './AIChatMessage'
import { AIChatWelcome } from './AIChatWelcome'

import styles from './AIChat.module.scss'

type AIChatBotAPIProps = {
  className?: string
  integrationId: string
  prompts?: AIChatPrompt[] | null
}

const AIChatBotAPIInner: FC<Omit<AIChatBotAPIProps, 'integrationId'>> = ({
  className,
  prompts,
}) => {
  const refInput = useRef<HTMLTextAreaElement>(null)
  const [isEmpty, setIsEmpty] = useState(true)
  const [isShowScroll, setIsShowScroll] = useState(false)
  const [refLast, isInEnd, elLast] = useInView()

  const isMounted = useDidMount()

  const { visibleMessages, isLoading, appendMessage } = useCopilotChat()

  const scrollToEnd = useCallback(
    (behavior: 'smooth' | 'instant' = 'smooth') => {
      elLast?.target?.scrollIntoView({ behavior })
    },
    [elLast?.target]
  )

  useEffect(() => {
    const input = refInput.current

    const handleKeyEnter = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !isEmpty && !isLoading) {
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

  const handleSend = useCallback(async () => {
    if (!refInput?.current?.value || isLoading) {
      return
    }

    const messageContent = refInput.current.value

    // Send message via CopilotKit using TextMessage
    await appendMessage(
      new TextMessage({
        role: MessageRole.User,
        content: messageContent,
      })
    )

    setIsEmpty(true)

    if (refInput.current) {
      refInput.current.value = ''
      refInput.current.focus()
    }
  }, [appendMessage, isLoading])

  const handleSubmit: FormEventHandler<HTMLFormElement> = useCallback(
    (e) => {
      e.preventDefault()
      if (isEmpty || isLoading) {
        return
      }
      handleSend()
    },
    [handleSend, isEmpty, isLoading]
  )

  // Filter to only user and assistant messages (skip system/function messages)
  const chatHistory = visibleMessages.filter(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (msg: any) => msg.role === MessageRole.User || msg.role === MessageRole.Assistant
  )

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

  const isBlocked = isEmpty || isLoading

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.body}>
        <Show if={!chatHistory?.length}>
          <AIChatWelcome className={styles.welcome} />
        </Show>

        <Show if={chatHistory?.length}>
          <ul className={styles.list}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {chatHistory.map((message: any) => (
              <li className={styles.item} key={message.id}>
                <AIChatMessage message={message} className={styles.message} />
              </li>
            ))}
          </ul>

          <Show if={isLoading}>
            <span className={styles.service}>Thinking...</span>
          </Show>

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
          [styles.warming]: !chatHistory.length && isLoading,
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
                disabled={!refInput.current || isLoading}
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
          className={clsx(styles.input, { [styles.blocked]: isLoading })}
          autoFocus={true}
          autoComplete="off"
          placeholder="How can I help you?"
          ref={refInput}
          onChange={handleChange}
          onFocus={handleFocus}
          name="message"
          indicator={isLoading ? <Loader className={styles.indicator} /> : null}
        />
        <button type="submit" className={styles.submit} disabled={isBlocked}>
          <IconSend className={styles.icon} />
        </button>
      </form>

      <Show if={!chatHistory.length && isLoading}>
        <div className={clsx(styles.footer, styles.loading)}>
          <Loader className={styles.loader} />
        </div>
      </Show>
    </div>
  )
}

export const AIChatBotAPI: FC<AIChatBotAPIProps> = ({ integrationId, ...props }) => {
  return (
    <CopilotKit
      runtimeUrl={`/api/copilotkit/${integrationId}`}
      showDevConsole={false}
      agent="agentic_chat">
      <AIChatBotAPIInner {...props} />
    </CopilotKit>
  )
}
