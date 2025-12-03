'use client'

import { CSSProperties, FC } from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import { marked } from 'marked'

import ImageFallback from '@/components/atoms/ImageFallback'
import Text from '@/components/atoms/Text'
import { WarehouseDashboardBySlugClient } from '@/components/feature/WarehouseDashboard'
import Button, { ButtonSize, ButtonVariant } from '@/components/ui/Button'
import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import { Session } from '@/lib/session'
import { replaceTemplateVariables } from '@/utils/strings'

import FormField from '../../FormField'
import { FormFieldInputSize } from '../../FormField/FormField'
import { TaskFormFieldExternalWallet } from '../fields/externalWallet/externalWallet'
import { TaskFormFieldFileS3 } from '../fields/fileS3/fileS3'
import { TaskFormFieldNFT } from '../fields/nft/TaskFormFieldNFT'
import { TaskFormFieldToken } from '../fields/token/TaskFormFieldToken'
import { TaskFormVariable } from '../types'
import { TaskFormDeployedLayout } from './TaskFormDeployedLayout'
import { TaskFormDeployedComponent } from './types'

import styles from './TaskFormDeployed.module.scss'

const getTextInputTypeByField = (field: TaskFormDeployedComponent): 'text' | 'email' | 'tel' => {
  if (field.type === 'textfield') {
    if (field.validate?.validationType === 'email') {
      return 'email'
    }

    if (field.validate?.validationType === 'phone') {
      return 'tel'
    }
  }

  return (field.properties?.type ?? 'text') as 'text'
}

export const TaskFormDeployedField: FC<{
  className?: string
  field: TaskFormDeployedComponent
  variables?: Record<string, TaskFormVariable>
  session?: Session | null
  onFormComplete?: (params?: {
    business_key?: string
    variables: Record<string, TaskFormVariable>
  }) => void
}> = ({ className, field, variables, session, onFormComplete }) => {
  const replaceTemplateVars = (text: string) => replaceTemplateVariables(text, variables)

  const { label, description, type } = field
  const commonClassName = clsx(styles.field, styles[type], className)
  const labelParsed = replaceTemplateVars(label ?? '')
  const descriptionParsed = replaceTemplateVars(description ?? '')

  const setFormBodyEnabled = (form?: HTMLFormElement | null, state = true) => {
    const formBody = form?.querySelector(':scope > fieldset') as HTMLFieldSetElement

    if (!formBody) {
      return
    }

    formBody.disabled = !state
  }

  switch (field.type) {
    case 'group': {
      return (
        <FormField
          type="custom"
          tooltip={descriptionParsed ?? undefined}
          caption={labelParsed}
          className={commonClassName}>
          <Show if={field.properties?.type === 'dashboard'}>
            <WarehouseDashboardBySlugClient
              slug={`${field.properties?.slug || ''}`}
              showTitle={false}
            />
          </Show>

          <Show if={!['dashboard'].includes(field.properties?.type ?? '')}>
            <TaskFormDeployedLayout
              onFormComplete={onFormComplete}
              session={session}
              components={field.components}
              variables={variables}
              className={clsx(commonClassName, styles.group, {
                [styles.outline]: field.showOutline,
              })}
              style={
                {
                  maxWidth: field.properties?.maxWidth || undefined,
                  margin: field.properties?.maxWidth ? '0 auto' : undefined,
                } as CSSProperties
              }
            />
          </Show>
        </FormField>
      )
    }

    case 'iframe': {
      return (
        <FormField
          type="custom"
          tooltip={descriptionParsed ?? undefined}
          caption={labelParsed}
          className={commonClassName}>
          <iframe src={field.url} height={field.height || 300} className={styles.iframe} />
        </FormField>
      )
    }

    case 'text': {
      const parsedMarkup = DOMPurify.sanitize(
        marked.parse(field.text ?? '', { async: false }) as string
      )

      return (
        <Text
          dangerouslySetInnerHTML={{ __html: replaceTemplateVars(parsedMarkup) }}
          className={clsx(commonClassName, styles.message)}
        />
      )
    }

    case 'html': {
      const content = DOMPurify.sanitize(field.content ?? '', {
        ADD_TAGS: ['iframe', 'style', 'svg'],
        ADD_ATTR: ['allow', 'allowfullscreen', 'target'],
        FORCE_BODY: true,
      }) as string

      return (
        <Text
          className={commonClassName}
          dangerouslySetInnerHTML={{ __html: replaceTemplateVars(content) }}
        />
      )
    }

    case 'image':
      return <ImageFallback className={commonClassName} fallback={null} src={field.source} />

    case 'textarea':
    case 'textfield': {
      if (['token', 'nft', 'wallet'].includes(field.properties?.type ?? '')) {
        return (
          <FormField type="custom" tooltip={descriptionParsed ?? undefined} caption={labelParsed}>
            <Show if={field.properties?.type === 'token'}>
              <TaskFormFieldToken name={field.key ?? 'token'} />
            </Show>
            <Show if={field.properties?.type === 'nft'}>
              <TaskFormFieldNFT name={field.key ?? 'nft'} />
            </Show>
            <Show if={field.properties?.type === 'wallet'}>
              <TaskFormFieldExternalWallet name={field.key ?? 'wallet'} />
            </Show>
          </FormField>
        )
      }

      const defaultValue = field.properties?.value ?? field.defaultValue ?? undefined

      return (
        <FormField
          tooltip={descriptionParsed ?? undefined}
          caption={labelParsed}
          {...field.properties}
          name={field.key ?? undefined}
          type={
            field?.properties?.type === 'markdown'
              ? 'markdown'
              : field.type === 'textarea'
                ? 'textarea'
                : getTextInputTypeByField(field)
          }
          minLength={field.validate?.minLength}
          maxLength={field.validate?.maxLength}
          required={field.validate?.required}
          pattern={
            field.type === 'textfield' && field.validate?.validationType === 'phone'
              ? '([+]?\\d{1,2}[-\\s]?|)\\d{3}[-\\s]?\\d{3}[-\\s]?\\d{4}'
              : field.validate?.pattern
          }
          readOnly={field.readonly === 'on'}
          disabled={field.disabled}
          className={commonClassName}
          defaultValue={defaultValue ? replaceTemplateVars(defaultValue) : undefined}
          placeholder={replaceTemplateVars(field.properties?.placeholder || '')}
          prefix={field.type === 'textfield' ? field.appearance?.prefixAdorner : undefined}
          suffix={field.type === 'textfield' ? field.appearance?.suffixAdorner : undefined}
          size={
            field.type === 'textfield' ? (field.properties?.size as FormFieldInputSize) : undefined
          }
        />
      )
    }

    case 'datetime': {
      return (
        <FormField
          tooltip={descriptionParsed ?? undefined}
          caption={field.dateLabel}
          name={field.key ?? undefined}
          type={field.subtype || 'date'}
          required={field.validate?.required}
          readOnly={field.readonly === 'on'}
          disabled={field.disabled}
          className={commonClassName}
          defaultValue={field.properties?.value ?? field.defaultValue ?? undefined}
        />
      )
    }

    case 'number':
      return (
        <FormField
          tooltip={descriptionParsed ?? undefined}
          name={field.key ?? undefined}
          caption={labelParsed}
          type="number"
          min={field.validate?.min}
          max={field.validate?.max}
          required={field.validate?.required}
          readOnly={field.readonly === 'on'}
          disabled={field.disabled}
          className={commonClassName}
          defaultValue={field.properties?.value ?? field.defaultValue ?? undefined}
          placeholder={field.properties?.placeholder}
          prefix={field.appearance?.prefixAdorner}
          suffix={field.appearance?.suffixAdorner}
        />
      )

    case 'select':
      return (
        <FormField
          tooltip={descriptionParsed ?? undefined}
          name={field.key ?? undefined}
          caption={labelParsed}
          type="select"
          required={field.validate?.required}
          disabled={field.disabled}
          options={field.values}
          className={commonClassName}
        />
      )

    case 'checkbox':
      return (
        <FormField
          defaultChecked={field.defaultValue ?? undefined}
          value={field.properties?.value ?? undefined}
          tooltip={descriptionParsed ?? undefined}
          name={field.key ?? undefined}
          caption={labelParsed}
          type="checkbox"
          required={field.validate?.required}
          disabled={field.disabled}
          className={commonClassName}
        />
      )

    case 'filepicker': {
      const fieldProps = {
        name: field.key ?? undefined,
        tooltip: descriptionParsed ?? undefined,
        size: (field.properties?.size as FormFieldInputSize) ?? undefined,
        caption: labelParsed,
        multiple: field.multiple === 'on',
        accept: field.accept,
        required: field.validate?.required,
        disabled: field.disabled,
        className: commonClassName,
      }

      if (field.properties?.type === 's3') {
        const handlePending = (input: HTMLInputElement) => {
          setFormBodyEnabled(input.form, false)
        }

        const handleComplete = (input: HTMLInputElement) => {
          setFormBodyEnabled(input.form, true)
        }

        return (
          <TaskFormFieldFileS3
            type="file"
            {...fieldProps}
            defaultValue={field.properties?.value}
            onPending={handlePending}
            onComplete={handleComplete}
          />
        )
      }

      return <FormField type="file" {...fieldProps} />
    }

    case 'checklist':
    case 'radio':
      return (
        <FormField
          type="custom"
          tooltip={descriptionParsed ?? undefined}
          caption={labelParsed}
          className={commonClassName}>
          <ul
            className={clsx(styles.checklist, {
              [styles[field.properties?.type || '']]: !!field.properties?.type,
            })}>
            {field.values?.map((item, idx) => {
              const isDefaultChecked = field.defaultValue === item.value

              return (
                <li className={styles.checklistItem} key={item.value}>
                  {field.properties?.type === 'color' && (
                    <label
                      className={styles.colorChoose}
                      style={{ '--_color': item.value } as CSSProperties}>
                      <input
                        required={field.validate?.required && idx === 0 ? true : undefined}
                        className={styles.colorChooseControl}
                        type="radio"
                        value={item.value}
                        name={field.key ?? undefined}
                        defaultChecked={isDefaultChecked}
                      />
                      <span className={styles.colorChooseCaption}>
                        {replaceTemplateVars(item.label)}
                      </span>
                    </label>
                  )}

                  {field.properties?.type !== 'color' && (
                    <FormField
                      required={field.validate?.required && idx === 0 ? true : undefined}
                      type={type === 'radio' ? 'radio' : 'checkbox'}
                      name={field.key ?? undefined}
                      caption={replaceTemplateVars(item.label)}
                      className={styles.checklistCheck}
                      defaultChecked={isDefaultChecked}
                      value={item.value}
                    />
                  )}
                </li>
              )
            })}
          </ul>
        </FormField>
      )

    case 'separator':
      return <hr className={clsx(styles.separator, commonClassName)} />

    case 'spacer':
      return null

    case 'button': {
      const commonProps = {
        caption: !session ? 'Login to continue' : labelParsed,
        className: commonClassName,
        isBlock: true,
        variant: (field.properties?.variant ??
          (field.action === 'submit' ? 'primary' : 'secondary')) as ButtonVariant,
        size: (field.properties?.size as ButtonSize) || 'xl',
        disabled: field.disabled,
      }

      const href = field.properties?.href

      if (href) {
        return (
          <Button {...commonProps} href={href} target={field.properties?.target ?? undefined} />
        )
      }

      return (
        <Button
          {...commonProps}
          onClick={
            field.properties?.type === 'cancel' || field.properties?.value === 'back'
              ? (e) => {
                  e.preventDefault()
                  const submitter = e.currentTarget as HTMLButtonElement
                  const variables = { [submitter.name]: { value: submitter.value } }
                  console.log('Cancel button clicked:', { submitter, variables, onFormComplete })
                  onFormComplete?.({ variables })
                }
              : undefined
          }
          name={field.properties?.name ?? field.key ?? undefined}
          value={field.properties?.value ?? undefined}
          type={field.action}
        />
      )
    }

    default:
      return (
        <FormField
          type="custom"
          tooltip={descriptionParsed ?? undefined}
          caption={labelParsed}
          className={commonClassName}>
          <Message type="danger">
            Unknown field type <code>{type}</code>
          </Message>
        </FormField>
      )
  }
}
