'use client'

import Image from 'next/image'
import Link from 'next/link'

import { FC, FormEventHandler, SyntheticEvent, useEffect, useMemo, useState } from 'react'

import { CaipAddress } from '@reown/appkit'
import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import noop from 'lodash/noop'
import { marked } from 'marked'
import { toast } from 'react-toastify'
import { isAddress, isHash } from 'viem'

import { fetchTokens } from '@/actions/tokens'
import Loader from '@/components/atoms/Loader'
import QrCodeAddress from '@/components/atoms/QrCodeAddress'
import FormField from '@/components/composed/FormField'
import GeneratedArt from '@/components/composed/GeneratedArt'
import { WarehouseDashboardBySlugClient } from '@/components/feature/WarehouseDashboard/WarehouseDashboardBySlug/WarehouseDashboardBySlugClient'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import { guruTestnet } from '@/config/wagmi'
import { WalletType, useWalletAddress } from '@/hooks/useWalletAddress'
import { FlowClientObject } from '@/services/flow'
import { getShortAddress } from '@/utils/strings'

import { getTaskFormDataToObject, getVariablesFromObject } from '..'
import LinkProfile from '../../LinkProfile'
import { LinkProfileProps } from '../../LinkProfile/LinkProfile'
import groupTaskFormVariables from '../../Quest/QuestTask/utils'
import StateMessage from '../../StateMessage'
import { TaskFormFieldCollection } from '../fields/collection/collection'
import { TaskFormFieldExternalWallet } from '../fields/externalWallet/externalWallet'
import { TaskFormFieldNFT } from '../fields/nft/TaskFormFieldNFT'
import { TaskFormFieldToken } from '../fields/token/TaskFormFieldToken'
import { TaskFormStakes } from '../stakes/TaskFormStakes'
import { TaskFormProps } from '../types'

import styles from '../TaskForm.module.scss'

const getTypeByVarType = (type: string) => {
  return type === 'Boolean'
    ? 'checkbox'
    : ['Short', 'Integer', 'Long', 'Double'].includes(type ?? '')
      ? 'number'
      : 'text'
}
export const TaskFormFromVarsForm: FC<TaskFormProps & { isStartForm?: boolean }> = ({
  title,
  description,
  icon,
  className,
  variables,
  onComplete,
  isLoading,
  isError,
  isStartForm,
  definitionKey,
  instanceId,
  session,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  // indicates whether share link was clicked or not.
  // User can't complete task until they click all share links
  const [linksToShare, setLinksToShare] = useState<Record<string, boolean>>({})
  const wallets = session?.user?.web3_wallets?.map((x) => x.wallet_address)
  const accountWallet = useWalletAddress(WalletType.thirdweb_ecosystem)

  const variablesGrouped = useMemo(() => groupTaskFormVariables(variables), [variables])

  useEffect(() => {
    if (variablesGrouped?.share) {
      setLinksToShare(
        Object.keys(variablesGrouped.share).reduce(
          (acc, key) => {
            acc[key] = false
            return acc
          },
          {} as Record<string, boolean>
        )
      )
    }
  }, [variablesGrouped])

  const isLoadedSuccessfully = !isError && !isLoading

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (
    e: SyntheticEvent<HTMLFormElement, SubmitEvent>
  ) => {
    e.preventDefault()
    setIsSubmitting(true)

    if (!variables || !Object.keys(variables ?? {})?.length) {
      toast.success('Task completed')
      onComplete?.()
      return
    }

    const submitter = e.nativeEvent.submitter as HTMLButtonElement
    const extra: Record<string, string | number | boolean | null> = {}

    if (
      submitter?.tagName === 'BUTTON' &&
      submitter?.name.startsWith('action_') &&
      variables[submitter.name]
    ) {
      extra[submitter.name] = submitter.value === 'true'
    }

    const newVariables = getVariablesFromObject(
      getTaskFormDataToObject(e.currentTarget, extra),
      variables
    )

    try {
      // TODO: workaround that needs to be unified
      let businessKey
      if (isStartForm && definitionKey === 'tokenPriceNotifications') {
        const tokenId = `${newVariables['form_tokenAddress'].value}`
        const tokens = await fetchTokens({ ids: [tokenId] })
        const token = tokens?.[0]
        const userId = session?.user?.id
        businessKey = `${userId}-${tokenId}-${token?.symbols[0].toLowerCase()}`
      }

      onComplete?.({ business_key: businessKey, variables: newVariables })
    } catch (error) {
      console.error('Error submitting form:', error)
      toast.error('Error submitting form')
    } finally {
      setIsSubmitting(false)
      console.log('Completed task')
    }
  }

  const parsedMarkup = DOMPurify.sanitize(
    marked.parse(description ?? '', {
      async: false,
    }) as string
  )

  return (
    <form
      className={clsx(styles.container, className)}
      onSubmit={!isLoading && !isSubmitting ? handleSubmit : noop}>
      <Show if={title || description || icon}>
        <div className={styles.header}>
          <Show if={icon}>
            <Image
              src={icon ?? ''}
              alt={description ?? ''}
              width={96}
              height={96}
              className={styles.icon}
            />
          </Show>

          <Show if={title}>
            <Caption variant="header" size="lg" className={styles.title}>
              {title}
            </Caption>
          </Show>

          <Show if={description}>
            <div className={styles.subtitle} dangerouslySetInnerHTML={{ __html: parsedMarkup }} />
          </Show>
        </div>
      </Show>

      <fieldset className={styles.body} disabled={!session}>
        <Show if={isLoading}>
          <Loader className={styles.loader} />
        </Show>
        <Show if={isError}>
          <StateMessage
            type="danger"
            className={styles.message}
            caption="Error while fetching task data"
          />
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
                    <GeneratedArt generatedArtId={varValue} isShareable />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.token}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.token ?? {})?.map(([varName, varData]) => {
                let valueObj

                try {
                  valueObj = JSON.parse(varData.value as string)
                } catch {
                  valueObj = undefined
                }

                return (
                  <li className={styles.item} key={varName}>
                    <TaskFormFieldToken
                      className={styles.token}
                      caption={varData.label}
                      name={varName}
                      account={accountWallet || ''}
                      tokenId={varData.value as string}
                      tokenList={valueObj}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.nft}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.nft ?? {})?.map(([varName, varData]) => {
                let valueObj: CaipAddress[] | undefined

                try {
                  valueObj = JSON.parse(varData.value as string)
                } catch {
                  valueObj = undefined
                }

                const externalWalletAddress =
                  (Object.values(variablesGrouped?.externalWallet ?? {})?.[0]?.value as string) ||
                  null

                return (
                  <li className={styles.item} key={varName}>
                    <TaskFormFieldNFT
                      className={styles.token}
                      caption={varData.label}
                      name={varName}
                      account={externalWalletAddress || accountWallet || ''}
                      address={varData.value as CaipAddress}
                      collectionList={valueObj}
                    />
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
                    {/* eslint-disable-next-line @next/next/no-img-element */}
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
                        href={
                          isHash(varValue)
                            ? `${guruTestnet.blockExplorers?.default.url}/tx/${varValue}`
                            : varValue
                        }
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
                        href={
                          isAddress(varValue)
                            ? `${guruTestnet.blockExplorers?.default.url}/address/${varValue}`
                            : varValue
                        }
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

          <Show if={variablesGrouped?.collection}>
            {Object.entries(variablesGrouped?.collection ?? {})?.map(([varName, varData]) => {
              return (
                <TaskFormFieldCollection
                  name={varName}
                  id={`${varData.value}`}
                  key={varName}
                  className={styles.collection}
                  title={varData.label}
                />
              )
            })}
          </Show>

          <Show if={variablesGrouped?.externalWallet}>
            {Object.entries(variablesGrouped?.externalWallet ?? {})?.map(([varName, varData]) => {
              return (
                <TaskFormFieldExternalWallet
                  name={varName}
                  key={varName}
                  className={styles.externalWallet}
                  title={varData.label}
                />
              )
            })}
          </Show>

          <Show if={variablesGrouped?.dashboard}>
            {Object.entries(variablesGrouped?.dashboard ?? {})?.map(([varName, varData]) => {
              const [slug, params] = `${varData.value}`.split('?')
              const paramsQuery = params ? new URLSearchParams(params) : null
              const paramsObj = paramsQuery ? Object.fromEntries(paramsQuery.entries()) : undefined

              return <WarehouseDashboardBySlugClient slug={slug} params={paramsObj} key={varName} />
            })}
          </Show>

          <Show if={variablesGrouped?.select}>
            {Object.entries(variablesGrouped?.select ?? {})?.map(([varName, varData]) => {
              const varValue = `${varData.value ?? ''}`

              const commonProps = {
                id: varName,
                name: varName,
                caption: varData.label || varName,
                defaultValue: varValue,
                className: styles.field,
              }
              const onSelectChange = (value: string | number) => {
                if (document && value) {
                  // if BPMN form field name is the same for Select_ and form_ prefixes
                  // then there is one way binding select -> changes form_ input
                  // i.e. select_wallet_address changes value form_wallet_address input
                  const formFieldName = varName.replace('select_', 'form_')

                  const formInput = document.getElementById(
                    formFieldName
                  ) as HTMLInputElement | null
                  if (formInput) {
                    formInput.value = `${value}`
                  }
                }
              }

              if (wallets?.length) {
                return (
                  <FormField
                    key={varName}
                    {...commonProps}
                    onValueChange={onSelectChange}
                    options={wallets.map((x) => ({ value: x, label: getShortAddress(x) }))}
                    type="select"
                    required={varData.type !== 'Boolean'}
                  />
                )
              }
            })}
          </Show>

          <Show if={variablesGrouped?.form}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.form ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`

                const commonProps = {
                  id: varName,
                  name: varName,
                  caption: varData.label || varName,
                  defaultValue: varValue,
                  className: styles.field,
                }

                const formFieldType = getTypeByVarType(varData.type ?? '')

                return (
                  <li className={styles.item} key={varName}>
                    <Show if={varData.type !== 'Boolean'}>
                      <input type="hidden" name={varName} value="" />
                    </Show>

                    <FormField
                      {...commonProps}
                      type={varName.endsWith('_markdown') ? 'markdown' : formFieldType}
                      required={varData.type !== 'Boolean'}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.formmultiline}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.formmultiline ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`

                const commonProps = {
                  id: varName,
                  name: varName,
                  caption: varData.label || varName,
                  defaultValue: varValue,
                  className: styles.field,
                }

                return (
                  <li className={styles.item} key={varName}>
                    <FormField
                      {...commonProps}
                      type={varName.endsWith('_markdown') ? 'markdown' : 'textarea'}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.message}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.message ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`
                if (!varValue && !varData.label) {
                  return null // Skip if there's no value nor label
                }

                const isLink = varName?.startsWith('link_')

                if (isLink) {
                  return (
                    <li className={styles.item} key={varName}>
                      <Message type="display" caption={varData.label} className={styles.display}>
                        <Link
                          href={varValue}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.link}>
                          {varValue}
                        </Link>
                      </Message>
                    </li>
                  )
                }

                const parsedVarMarkup = marked
                  .parse(varValue, {
                    async: false,
                  })
                  .replace(
                    /<a .*href="(.*)">/gm,
                    '<a href="$1" target="_blank" rel="noopener noreferrer">'
                  )

                return (
                  <li className={styles.item} key={varName}>
                    <Message
                      type="display"
                      caption={varData.label}
                      className={styles.display}
                      dangerouslySetInnerHTML={{ __html: parsedVarMarkup }}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.stakes}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.stakes ?? {})?.map(([varName, varData]) => {
                let data

                try {
                  data = JSON.parse(varData.value as string)
                } catch {
                  data = {}
                }

                const withdrawTime = variables?.['withdraw_time']?.value || null
                if (withdrawTime) {
                  data.withdraw_time = withdrawTime
                }
                return (
                  <li className={styles.item} key={varName}>
                    <TaskFormStakes name={varName} caption={varData.label} data={data} />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.web3}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.form ?? {})?.map(([varName, varData]) => {
                const varValue = `${varData.value ?? ''}`

                const commonProps = {
                  id: varName,
                  name: varName,
                  caption: varData.label || varName,
                  defaultValue: varValue,
                  className: styles.field,
                }

                const formFieldType = getTypeByVarType(varData.type ?? '')

                return (
                  <li className={styles.item} key={varName}>
                    <FormField
                      {...commonProps}
                      type={formFieldType}
                      required={varData.type !== 'Boolean'}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.share}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.share ?? {}).map(([varName, varData]) => {
                const varLabel = varData.label || varName
                const varValue = `${varData.value ?? ''}` // This will be the href link

                if (!varValue) {
                  return null // Skip if there's no value
                }

                return (
                  <li className={styles.item} key={varName}>
                    <Button
                      onClick={() =>
                        setLinksToShare((prev) => {
                          const newLinks = { ...prev }
                          newLinks[varName] = true
                          return newLinks
                        })
                      }
                      isBlock
                      variant="primary"
                      size="xl"
                      href={varValue}
                      target="_blank"
                      rel="noopener noreferrer"
                      caption={varLabel}
                      className={styles.action}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.qrCode}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.qrCode ?? {}).map(([varName, varData]) => {
                const varLabel = varData.label || varName
                const varValue = `${varData.value ?? ''}` // This will be the address to render with qr code

                if (!varValue) {
                  return null // Skip if there's no value
                }

                return (
                  <li className={styles.item} key={varName}>
                    <QrCodeAddress
                      address={varValue}
                      caption={varLabel}
                      className={styles.action}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>
        </Show>
      </fieldset>

      <Show if={isLoadedSuccessfully}>
        <fieldset className={styles.footer}>
          <Show if={variablesGrouped?.redirect}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.redirect ?? {})?.map(([varName, varData]) => {
                const varLabel = varData.label || varName
                const varValue = `${varData.value ?? ''}`

                return (
                  <li className={styles.item} key={varName}>
                    <Button
                      isBlock
                      variant="primary"
                      size="xl"
                      type="submit"
                      caption={varLabel}
                      href={varValue}
                      target={
                        varValue.includes(window.location.origin) || varValue.startsWith('/')
                          ? '_self'
                          : '_blank'
                      }
                      className={styles.action}
                      isPending={isLoading || isSubmitting}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>

          <Show if={variablesGrouped?.thirdwebLinkProfile}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.thirdwebLinkProfile ?? {})?.map(
                ([varName, varData]) => {
                  const varLabel = varData.label || varName
                  const varValue = `${varData.value ?? ''}` as LinkProfileProps['social'] // This will be the profile type

                  return (
                    <li className={styles.item} key={varName}>
                      <LinkProfile
                        social={varValue}
                        caption={varLabel}
                        className={styles.action}
                        isBlock
                        variant="primary"
                        size="xl"
                        type="button"
                        onSuccess={async ({ username }) => {
                          // set form_xAccount variable in the process execution in camunda
                          if (varValue === 'x' && username && instanceId) {
                            await FlowClientObject.engine.proxy.put(
                              `process-instance/${instanceId}/variables/form_xAccount`,
                              { type: 'String', value: username }
                            )
                          }
                        }}
                      />
                    </li>
                  )
                }
              )}
            </ul>
          </Show>

          <Show if={!variablesGrouped?.action}>
            <Button
              isBlock
              variant="primary"
              size="xl"
              type="submit"
              isDisabled={Object.values(linksToShare).some((x) => !x)}
              isPending={isLoading || isSubmitting}>
              OK
            </Button>
          </Show>

          <Show if={variablesGrouped?.action}>
            <ul className={styles.list}>
              {Object.entries(variablesGrouped?.action ?? {})?.map(([varName, varData]) => {
                if (
                  definitionKey === 'form_review_stakes' &&
                  ['action_withdraw', 'action_claim'].includes(varName)
                ) {
                  return null // do not render action buttons. they are rendered in TaskFormStakes.tsx
                }

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
                      isDisabled={Object.values(linksToShare).some((x) => !x)}
                      className={styles.action}
                      isPending={isLoading || isSubmitting}
                    />
                  </li>
                )
              })}
            </ul>
          </Show>
        </fieldset>
      </Show>
    </form>
  )
}
