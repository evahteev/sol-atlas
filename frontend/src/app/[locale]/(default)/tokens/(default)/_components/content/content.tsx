'use client'

import { useRouter, useSearchParams } from 'next/navigation'

import { FC, PropsWithChildren, useEffect, useRef, useState } from 'react'

import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { useInViewRef } from 'rooks'

import FormField from '@/components/composed/FormField'
import Button from '@/components/ui/Button'
import Message from '@/components/ui/Message'
import Section from '@/components/ui/Section'
import Show from '@/components/ui/Show'
import Table from '@/components/ui/Table'
import { TableRowProps } from '@/components/ui/Table/types'
import { useTokenSearch } from '@/hooks/tokens/useTokenSearch'
import { useDidMount } from '@/hooks/useDidMount'
import { ChainModel } from '@/models/chain'
import { TokenTagModel, TokenV3Model } from '@/models/token'
import { getTokenSymbolsString } from '@/utils/tokens'

import { TokensTagsCloud } from '../cloud/cloud'
import { tokenSelectorColumns } from './columns'

import styles from './content.module.scss'

const REQUEST_LIMIT = 10

type TokensExplorerContentProps = PropsWithChildren<{
  className?: string
  chains?: ChainModel[]
  tags?: TokenTagModel[]
}>

export const TokensExplorerContent: FC<TokensExplorerContentProps> = ({
  className,
  chains,
  tags,
  children,
}) => {
  const router = useRouter()
  const searchParams = useSearchParams()
  const startQuery = searchParams.get('search') ?? ''

  const [refTags, isInViewTags] = useInViewRef()
  const [refTokens, isInViewTokens] = useInViewRef()
  const [query, setQuery] = useState(startQuery)

  const refInput = useRef<HTMLInputElement>(null)

  const { data, isLoading } = useTokenSearch({ query })
  const searchTokens = [
    ...(data ?? []),
    ...((isLoading ? Array(REQUEST_LIMIT) : []) as TokenV3Model[]),
  ]

  const { inputValue, getMenuProps, highlightedIndex, getItemProps, getInputProps } = useCombobox({
    items: searchTokens,
    itemToString: (item) => getTokenSymbolsString(item?.symbols ?? []),
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem) {
        return
      }
    },
    defaultInputValue: query,
    onInputValueChange: ({ inputValue: val }) => {
      router.replace(`?search=${val}`)
      setQuery(val)
    },
  })

  const getRowProps = (item?: TokenV3Model, index?: number): TableRowProps => {
    if (!item) {
      return {}
    }

    return {
      ...getItemProps({ item, index }),
      className: clsx({
        [styles.hilite]: highlightedIndex === index,
      }),
    }
  }

  const tagsList = tags?.filter((item) =>
    inputValue ? item.tag_name.toLowerCase().includes(inputValue.toLowerCase()) : true
  )

  const isMounted = useDidMount()
  useEffect(() => {
    if (!isMounted) {
      return
    }

    refInput.current?.focus()
  }, [isMounted])

  return (
    <>
      <div className={clsx(styles.container, { [styles.tokensOnly]: !tags }, className)}>
        <div className={styles.header}>
          <FormField
            placeholder="Search Tokens Or Tags"
            {...getInputProps({ ref: refInput })}
            size="lg"
            type="search"
            autoFocus
          />

          <Show if={inputValue && !!tags}>
            <div className={styles.tabs}>
              <Button
                href="#tags"
                variant="switch"
                size="sm"
                className={styles.tab}
                isActive={isInViewTags}>
                Tags
              </Button>
              <Button
                href="#tokens"
                variant="switch"
                size="sm"
                className={styles.tab}
                isActive={isInViewTokens && !isInViewTags}>
                Tokens
              </Button>
            </div>
          </Show>
        </div>
        <div className={styles.body} {...getMenuProps()}>
          <Show if={!inputValue && children}>{children}</Show>

          <Show if={inputValue || !children}>
            <div className={styles.content}>
              <Show if={tags}>
                <Section
                  id="tags"
                  className={styles.section}
                  classNames={{ header: styles.sectionHeader, body: styles.sectionBody }}
                  caption="Tags"
                  ref={refTags}>
                  <Show if={tagsList?.length}>
                    <TokensTagsCloud tags={tagsList} />
                  </Show>
                  <Show if={!tagsList?.length}>
                    <Message type="info" className={styles.message}>
                      No appropriate tags found
                    </Message>
                  </Show>
                </Section>
              </Show>

              <Section
                id="tokens"
                className={styles.section}
                classNames={{ header: styles.sectionHeader, body: styles.sectionBody }}
                caption={tags ? 'Tokens' : undefined}
                ref={refTokens}>
                <Show if={searchTokens?.length}>
                  <Table
                    className={styles.table}
                    data={searchTokens}
                    classNameTHead={styles.thead}
                    classNameTBody={styles.tbody}
                    classNameTCell={styles.tcell}
                    rowHref={(item) =>
                      item
                        ? `/token/${item?.network?.toLowerCase()}/${item?.address?.toLowerCase()}`
                        : ''
                    }
                    rowKey={(item) => item?.id}
                    rowProps={(data) => ({
                      'data-loading': !data || undefined,
                      ...getRowProps(),
                    })}
                    columns={tokenSelectorColumns(chains)}
                  />
                </Show>
                <Show if={!searchTokens?.length}>
                  <Message type="info" className={styles.message}>
                    No appropriate tokens found
                  </Message>
                </Show>
              </Section>
            </div>
          </Show>
        </div>
      </div>
    </>
  )
}
