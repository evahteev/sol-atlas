'use client'

import {
  ChangeEventHandler,
  FC,
  FormEventHandler,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'

import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { useTypewriter } from '@/hooks/useTypewriter'
import IconSend from '@/images/icons/send.svg'

import { WarehouseDashboardAnalyzerHistory } from './WarehouseDashboardAnalyzerHistoryProvider'
import { WarehouseDashboardAnalyzerVariants } from './WarehouseDashboardAnalyzerVariants'
import { useDashboardAnalyze } from './hooks'

import styles from './WarehouseDashboardAnalyzerChat.module.scss'

const WarehouseDashboardAnalyzerChat: FC<{
  className?: string
  slug: string
  params?: Record<string, unknown>
}> = ({ className, slug, params }) => {
  const { history, updateHistory } = useContext(WarehouseDashboardAnalyzerHistory)

  const [isSendDisabled, setIsSendDisabled] = useState(true)
  const [currentPrompt, setCurrentPrompt] = useState<string | null>(null)
  const refInput = useRef<HTMLInputElement>(null)

  const handleChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    setIsSendDisabled(!e.target.value.trim())
  }

  const { data, error, isFetching } = useDashboardAnalyze({
    slug,
    params,
    prompt: currentPrompt,
  })

  const handleSubmit: FormEventHandler = (e) => {
    e.preventDefault()
    if (!refInput.current || isFetching) {
      return
    }
    const value = refInput.current.value.trim()
    if (value) {
      setCurrentPrompt(value)
      setIsSendDisabled(true)
      refInput.current.value = ''
      refInput.current.focus()
    }
  }

  useEffect(() => {
    if (!currentPrompt || !data) {
      return
    }

    updateHistory({ prompt_submitted: currentPrompt, summary: data })
    setCurrentPrompt(null)

    if (refInput?.current) {
      refInput.current.focus()
    }
  }, [currentPrompt, data, updateHistory])

  const response =
    history?.length && data === history[history.length - 1].summary
      ? DOMPurify.sanitize(data.trim())
      : isFetching
        ? 'Hmmm... Let me think...'
        : error
          ? 'Ooops! Sorry, I got my circuits shorted...'
          : 'What do you want to know today?'

  const [printed, notPrinted] = useTypewriter(response)

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.body}>
        <ul className={styles.entries}>
          <Show if={!history.length && !currentPrompt}>
            <li className={styles.entry}>
              <div className={styles.response}>
                <div className={styles.text}>
                  <Show if={printed}>
                    <span className={styles.printed}>{printed}</span>
                    <span className={styles.notPrinted}>{notPrinted}</span>
                  </Show>
                </div>
              </div>
            </li>
          </Show>

          {history.map((entry, idx) => {
            if (data === entry.summary) {
              return null
            }

            return (
              <li className={styles.entry} key={idx}>
                <div className={styles.prompt}>
                  <div className={styles.text}>{entry.prompt_submitted}</div>
                </div>
                <div className={styles.response}>
                  <div className={styles.text}>{entry.summary}</div>
                </div>
              </li>
            )
          })}

          <Show if={currentPrompt}>
            <li className={styles.entry}>
              <div className={styles.prompt}>
                <div className={styles.text}>{currentPrompt}</div>
              </div>
              <div className={styles.response}>
                <div className={styles.text}>
                  <Show if={printed}>
                    <span className={styles.printed}>{printed}</span>
                    <span className={styles.notPrinted}>{notPrinted}</span>
                  </Show>

                  <Show if={isFetching}>
                    <div className={styles.processing}>
                      <span />
                      <span />
                    </div>
                  </Show>
                </div>
              </div>
            </li>
          </Show>

          <Show if={!!history?.length && !isFetching}>
            <li className={styles.entry}>
              <div className={styles.response}>
                <div className={styles.text}>What&apos;s next?</div>
              </div>
            </li>
          </Show>
        </ul>
      </div>

      <div className={styles.footer}>
        <WarehouseDashboardAnalyzerVariants
          className={styles.variants}
          slug={slug}
          params={params}
          history={history}
          isDisabled={isFetching}
          onSubmit={(value) => {
            setCurrentPrompt(value)
          }}
        />

        <form className={styles.input} onSubmit={handleSubmit}>
          <input
            className={styles.query}
            placeholder="Type your query"
            ref={refInput}
            onChange={handleChange}
            autoFocus
          />
          <Button
            size="lg"
            variant="clear"
            icon={<IconSend className={clsx(styles.icon, { [styles.disabled]: isSendDisabled })} />}
            className={styles.submit}
            disabled={isSendDisabled || isFetching}
          />
        </form>
      </div>
    </div>
  )
}

export default WarehouseDashboardAnalyzerChat
