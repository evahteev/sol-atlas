import { FC, ReactNode, useRef, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { useDebouncedValue, usePreviousDifferent } from 'rooks'

import { fetchTokensDefault, fetchTokensSearch } from '@/actions/tokens'
import FormField from '@/components/composed/FormField'
import { TokenModel } from '@/models/token'
import { getTokenSymbolsString } from '@/utils/tokens'

import { PageActionsSwapToken } from '../token/token'

import styles from './tokens.module.scss'

type PageActionsSwapTokensProps = {
  className?: string
  onChange: (token: TokenModel) => void
  caption?: ReactNode

  skipToken?: TokenModel
}

export const PageActionsSwapTokens: FC<PageActionsSwapTokensProps> = ({
  className,
  onChange,
  caption,
  skipToken,
}) => {
  const [query, setQuery] = useState('')
  const [debouncedQuery] = useDebouncedValue(query, 1000)

  const refInput = useRef<HTMLInputElement>(null)

  const searchNetwork = 'xfitest'

  const { data: defaultTokens } = useQuery({
    queryKey: [searchNetwork],
    queryFn: () => {
      return fetchTokensDefault(searchNetwork)
    },
  })

  const { data: searchTokens } = useQuery({
    queryKey: [debouncedQuery, searchNetwork],
    queryFn: () => {
      if (query.trim().length < 3) {
        return null
      }

      return fetchTokensSearch({
        query: debouncedQuery,
        network: searchNetwork,
      })
    },
  })

  const previousSearchTokens = usePreviousDifferent(searchTokens)

  const tokensTableData = (
    (debouncedQuery.length >= 3
      ? searchTokens || previousSearchTokens || defaultTokens
      : defaultTokens) || []
  ).filter((item) => item?.marketType === 'token' && item.id !== skipToken?.id)

  const { getMenuProps, highlightedIndex, getItemProps, getInputProps } = useCombobox({
    items: tokensTableData,
    itemToString: (item) => getTokenSymbolsString(item?.symbols || ''),
    onInputValueChange: ({ inputValue }) => {
      setQuery(inputValue || '')
    },
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem) {
        return
      }
      onChange?.(selectedItem)
    },
  })

  return (
    <div className={clsx(styles.container, className)}>
      <FormField type="text" caption={caption} {...getInputProps({ ref: refInput })} />
      <ul className={styles.list} {...getMenuProps()}>
        {tokensTableData?.map((item, index) => (
          <li
            className={clsx(styles.item, { [styles.hilite]: highlightedIndex === index })}
            key={item.id}
            {...getItemProps({ item, index })}>
            <PageActionsSwapToken className={styles.token} token={item} />
          </li>
        ))}
      </ul>
    </div>
  )
}
