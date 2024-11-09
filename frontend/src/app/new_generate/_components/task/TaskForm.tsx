'use client'

import Link from 'next/link'

import { FC, FormEventHandler, SyntheticEvent, useState } from 'react'

import clsx from 'clsx'
import { noop } from 'lodash'
import { toast } from 'react-toastify'

import { getTaskVariables } from '@/actions/engine'
import GeneratedArt from '@/app/generate/components/GeneratedArt/GeneratedArt'
import Loader from '@/components/atoms/Loader'
import FormField from '@/components/composed/FormField'
import { Avatar, Button, Caption, Show } from '@/components/ui'
import Message from '@/components/ui/Message'
import { taskCustomComponent } from '@/config/custom'
import { tGuru } from '@/config/wagmi'
import { useTaskVariables } from '@/services/flow/hooks/engine'
import { getShortAddress } from '@/utils/strings'

import styles from './TaskForm.module.scss'

export type TaskFormCustomProps = TaskFormProps & {
  variables?: Awaited<ReturnType<typeof getTaskVariables>>
  isLoading?: boolean
  isError?: boolean
}

type TaskFormProps = {
  className?: string
  title?: string
  icon?: string | null
  taskKey?: string | null
  flowKey?: string
  id: string
  onComplete?: (variables: Awaited<ReturnType<typeof getTaskVariables>>) => void
}

const getTypeByVarPrefix = (name: string) => {
  const prefix = name.match(/^([a-zA-Z]+)_(.*)/)?.[1]

  return prefix?.replace(/(text|link)/, 'form') ?? 'default'
}

const getTypeByVarType = (type: string) => {
  return type === 'Boolean'
    ? 'checkbox'
    : ['Short', 'Integer', 'Long', 'Double'].includes(type ?? '')
      ? 'number'
      : 'text'
}

export const TaskForm: FC<TaskFormProps> = (props) => {
  const { title, icon, id, taskKey, flowKey, className, onComplete } = props
  const { data: variables, isLoading, isError } = useTaskVariables(id)
  const CustomForm = taskKey ? taskCustomComponent[flowKey ?? '']?.[taskKey] : null

  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isLoading && !isError && CustomForm) {
    return <CustomForm {...props} variables={variables} isLoading={isLoading} isError={isError} />
  }

  const variablesGrouped = variables
    ? Object.entries(variables ?? {})?.reduce(
        (acc, [varName, varData]) => {
          const section = getTypeByVarPrefix(varName)
          if (!acc[section]) {
            acc[section] = {}
          }
          acc[section][varName ?? 'unknown'] = varData

          return acc
        },
        {} as Record<
          string,
          Record<
            string,
            {
              value: unknown
              type?: string | null
              label?: string | null
            }
          >
        >
      )
    : null

  const isLoadedSuccessfully = !isError && !isLoading

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (
    e: SyntheticEvent<HTMLFormElement, SubmitEvent>
  ) => {
    e.preventDefault()

    setIsSubmitting(true)

    try {
      if (!variables) {
        toast.success('Task completed')
        onComplete?.({})
        return // Exit the function after completing the task
      }

      const formData = new FormData(e.currentTarget)

      // console.log('FormData keys:', Array.from(formData.keys()));
      // // returns ['form_message']
      //
      // console.log('FormData values:', Array.from(formData.values()));
      // // returns ['nete form message text']
      //
      // console.log('Variables:',  variables);
      // // returns: {
      // //     "form_message": {
      // //         "value": "Buckle up! Shill, chill, meme, repeat. 🚀",
      // //         "type": "String",
      // //         "label": "Board",
      // //         "valueInfo": {}
      // //     }
      // // }

      if (formData.entries().next().done) {
        // Check if FormData is empty
        console.warn('FormData is empty. No data captured.')
        // Handle the case where FormData is empty, maybe by alerting the user or logging more details.
      }
      // Prepare the newVariables object
      const newVariables = Object.fromEntries(
        Object.keys(variables || {}).map((name) => {
          const { type = 'String', value = '', valueInfo = {} } = variables[name] || {}
          let newValue: string | number | boolean | object | null = formData.get(name) as
            | string
            | number
            | boolean
            | object
            | null

          // If formData doesn't have this field, retain the original value
          if (newValue === null) {
            newValue = value as string | number | boolean | object | null // Type assertion
          } else {
            // Determine the correct value type based on the Camunda variable type
            switch (type) {
              case 'Boolean':
                newValue = newValue === 'true'
                break
              case 'Integer':
              case 'Long':
                if (typeof newValue === 'string') {
                  newValue = parseInt(newValue, 10)
                } else {
                  newValue = value as number
                }
                break
              case 'Double':
                if (typeof newValue === 'string') {
                  newValue = parseFloat(newValue)
                } else {
                  newValue = value as number
                }
                break
              case 'Date':
                if (typeof newValue === 'string') {
                  newValue = new Date(newValue).toISOString()
                } else {
                  newValue = value as string
                }
                break
              case 'Json':
              case 'Object':
                if (typeof newValue === 'string') {
                  try {
                    newValue = JSON.parse(newValue)
                    if (
                      typeof newValue !== 'string' &&
                      typeof newValue !== 'number' &&
                      typeof newValue !== 'boolean' &&
                      newValue !== null
                    ) {
                      newValue = null
                    }
                  } catch (e) {
                    console.error('Invalid JSON:', e)
                    newValue = null
                  }
                } else {
                  newValue = value as object
                }
                break
              default:
                console.warn('Unsupported Variable Type in Form')
                newValue = newValue !== null ? newValue : (value as string)
                break
            }
          }

          return [
            name,
            {
              type: type,
              valueInfo: valueInfo,
              value: newValue,
            },
          ]
        })
      )

      const submitter = e.nativeEvent.submitter as HTMLButtonElement

      if (
        submitter?.tagName === 'BUTTON' &&
        submitter?.name.startsWith('action_') &&
        variables[submitter.name]
      ) {
        const { type, valueInfo } = variables[submitter.name]

        // Add the action button variable to the newVariables object
        newVariables[submitter.name] = {
          type: type || 'Boolean',
          valueInfo: valueInfo || null,
          value: submitter.value === 'true',
        }
      }

      console.log('New Variables before Task Form complete:', newVariables)

      onComplete?.(newVariables)
    } catch (error) {
      console.error('Error submitting form:', error)
      toast.error('Error submitting form')
    } finally {
      setIsSubmitting(false)
      console.log('Completed task')
    }
  }

  return (
    <form
      className={clsx(styles.container, className)}
      onSubmit={!isLoading && !isSubmitting ? handleSubmit : noop}>
      <Show if={title || icon}>
        <div className={styles.header}>
          <Show if={icon}>
            <Avatar src={icon ?? ''} alt={title ?? ''} className={styles.icon} />
          </Show>

          <Caption variant="header" size="lg" className={styles.title}>
            {title}
          </Caption>
        </div>
      </Show>
      <div className={styles.body}>
        <Show if={isLoading}>
          <Loader className={styles.loader} />
        </Show>
        <Show if={isError}>
          <Message type="danger" className={styles.message}>
            Error while fetching task data
          </Message>
        </Show>

        <Show if={isLoadedSuccessfully}>
          <Show if={variablesGrouped?.art}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.art ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue) {
                  return null
                }

                return (
                  <li className={styles.item} key={varName}>
                    <GeneratedArt generatedArtId={varValue} />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.img}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.img ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue) {
                  return null
                }

                return (
                  <li className={styles.item} key={varName}>
                    {/* 
                          SHOULD BE <img> not <Image> or app will CRASH!
                          That happens because <Image> attributes 'width' and 'height' are not optional, but we don't know them
                       */}
                    <img className={styles.image} src={varValue} alt={varData.label ?? ''} />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.video}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.video ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue) {
                  return null
                }

                return (
                  <li className={styles.item} key={varName}>
                    <video
                      controls
                      controlsList="nofullscreen nodownload noremoteplayback noplaybackrate"
                      autoPlay
                      muted
                      loop
                      className={styles.video}
                      src={varValue}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.txhash}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.txhash ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue) {
                  return null
                }

                return (
                  <li className={styles.item} key={varName}>
                    <div className={styles.blockchain}>
                      Transaction{' '}
                      <Link
                        className={styles.scanLink}
                        href={`${tGuru.blockExplorers.default.url}/tx/${varValue}`}
                        target="_blank"
                        rel="noopener noreferrer">
                        {getShortAddress(varValue)}
                      </Link>
                    </div>
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.addrhash}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.txhash ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue) {
                  return null
                }

                return (
                  <li className={styles.item} key={varName}>
                    <div className={styles.blockchain}>
                      Address{' '}
                      <Link
                        className={styles.scanLink}
                        href={`${tGuru.blockExplorers.default.url}/address/${varValue}`}
                        target="_blank"
                        rel="noopener noreferrer">
                        {getShortAddress(varValue)}
                      </Link>
                    </div>
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.form}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.form ?? {})?.map(([varName, varData]) => {
                const isText = varName?.startsWith('text_')
                const isLink = varName?.startsWith('link_')
                const isTextOrLink = isText || isLink

                const varValue = `${varData.value ?? ''}`

                const commonProps = {
                  id: varName,
                  name: varName,
                  caption: varData.label || varName,
                  defaultValue: isTextOrLink ? undefined : varValue,
                  className: styles.field,
                }

                if (isTextOrLink) {
                  return (
                    <li className={styles.item} key={varName}>
                      <FormField
                        {...commonProps}
                        type="display"
                        value={
                          isLink ? (
                            <Link
                              href={varValue}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={styles.link}>
                              {varValue}
                            </Link>
                          ) : (
                            `${varData.value ?? ''}`
                          )
                        }
                      />
                    </li>
                  )
                }

                return (
                  <li className={styles.item} key={varName}>
                    <FormField {...commonProps} type={getTypeByVarType(varData.type ?? '')} />
                  </li>
                )
              })}
            </ul>
          </Show>
        </Show>
      </div>
      <Show if={isLoadedSuccessfully}>
        <div className={styles.footer}>
          <Show if={!variablesGrouped?.action}>
            <Button
              isBlock
              variant="main"
              size="xl"
              type="submit"
              isPending={isLoading || isSubmitting}>
              Complete task
            </Button>
          </Show>

          <Show if={variablesGrouped?.action}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.action ?? {})?.map(([varName, varData]) => {
                const varLabel = varData.label || varName

                return (
                  <li className={styles.item} key={varName}>
                    <Button
                      isBlock
                      variant="primary"
                      size="xl"
                      type="submit"
                      caption={varLabel}
                      value="true"
                      name={varName}
                      className={styles.action}
                      isPending={isLoading || isSubmitting}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>
        </div>
      </Show>
    </form>
  )
}
