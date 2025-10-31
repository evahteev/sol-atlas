'use client'

import { useRouter } from 'next/navigation'

import { FC, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { useDebouncedValue, useKey, usePreviousDifferent } from 'rooks'
import { UrlObject, format } from 'url'

import TokenAsset from '@/components/atoms/TokenAsset'
import DropdownContent from '@/components/ui/DropdownContent'
import Show from '@/components/ui/Show'
import { Table } from '@/components/ui/Table/Table'
import { TableRowProps } from '@/components/ui/Table/types'
import { useTokenSearch } from '@/hooks/tokens/useTokenSearch'
import { useTokensDefault } from '@/hooks/tokens/useTokensDefault'
import { useWalletTotals } from '@/hooks/useWalletTotals'
import IconDown from '@/images/icons/chevron-down.svg'
import { ChainModel } from '@/models/chain'
import { TokenV3Model, TokenV3ModelWithBalances } from '@/models/token'
import { AppContext } from '@/providers/context'
import { getBalanceFromList } from '@/utils/tokens'

import StateMessage from '../StateMessage'
import { tokenSelectorColumns } from './columns'

import styles from './TokenSelector.module.scss'

type TokenSelectorProps = {
  className?: string
  token?: TokenV3Model
  account?: string
  rowHref?:
    | (string | UrlObject | null)
    | ((token?: TokenV3Model, idx?: number) => string | UrlObject | null)
  onTokenChange?: (token?: TokenV3Model) => void
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
  chains?: ChainModel[]
  includeNative?: boolean
  initialData?: {
    balances?: {
      tokens?: TokenV3ModelWithBalances[]
      natives?: TokenV3ModelWithBalances[]
    }
  }
  tokenList?: TokenV3Model[]
}

export const TokenSelector: FC<TokenSelectorProps> = ({
  className,
  token,
  account,
  rowHref,
  placeholder = 'Search token by address or ticker',
  onTokenChange,
  size = 'lg',
  chains,
  includeNative,
  initialData,
  tokenList,
}) => {
  const { chains: allChains } = useContext(AppContext)
  const usedChains = chains ?? allChains

  const router = useRouter()

  const [currentToken, setCurrentToken] = useState<TokenV3Model | undefined>(token)

  useEffect(() => {
    if (token?.id === currentToken?.id) {
      return
    }

    setCurrentToken(token)
  }, [currentToken?.id, token])

  const { tokens, natives, isFetching } = useWalletTotals({
    address: account,
    chains: usedChains,
    refetchInterval: 5 * 60 * 1000,
    initialData: initialData?.balances,
  })

  const balances = useMemo(() => [...tokens, ...natives], [natives, tokens])

  const [query, setQuery] = useState('')
  const [debouncedQuery] = useDebouncedValue(query, 1000)

  const refContainer = useRef<HTMLDivElement>(null)

  const inputRef = useRef<HTMLInputElement>(null)
  const searchChains = usedChains?.map((chain) => chain.name).join(',')

  const { data: defaultTokens, isLoading: isDefaultTokensLoading } = useTokensDefault(
    {
      network: searchChains,
      include_native: includeNative,
    },
    {
      enabled: !tokenList?.length,
    }
  )

  const { data: searchTokens, isLoading: isSearchTokensLoading } = useTokenSearch(
    {
      query: debouncedQuery,
      network: searchChains,
      include_native: includeNative,
    },
    { enabled: !!debouncedQuery.length && !tokenList?.length }
  )

  const previousSearchTokens: TokenV3Model[] | null | undefined = usePreviousDifferent(searchTokens)

  const tokensTableData =
    tokenList?.filter(
      (token) =>
        token.address?.toLocaleLowerCase().includes(query.toLocaleLowerCase()) ||
        token.name?.toLocaleLowerCase().includes(query.toLocaleLowerCase()) ||
        token.description?.toLocaleLowerCase().includes(query.toLocaleLowerCase())
    ) ??
    (
      (debouncedQuery.length
        ? searchTokens || previousSearchTokens || defaultTokens
        : defaultTokens) || []
    ).filter((item) => item?.marketType === 'token')

  const {
    isOpen,
    openMenu,
    getToggleButtonProps,
    getMenuProps,
    highlightedIndex,
    getItemProps,
    getInputProps,
  } = useCombobox({
    items: tokensTableData,
    itemToString: () => '',
    onInputValueChange: ({ inputValue }) => {
      setQuery(inputValue.trim() || '')
    },
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem || selectedItem?.id === currentToken?.id) {
        return
      }

      setCurrentToken(selectedItem)
      if (rowHref) {
        router.push(format((typeof rowHref === 'function' ? rowHref(selectedItem) : rowHref) ?? ''))
      }

      onTokenChange?.(selectedItem)
    },
  })

  useKey(['Backquote', 'IntlBackslash'], () => {
    setTimeout(openMenu, 50)
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

  const getRowVars = useCallback(
    (item?: TokenV3Model): TableRowProps => {
      if (!item || !balances) {
        return {}
      }

      return {
        balance: getBalanceFromList(balances, item),
      }
    },
    [balances]
  )

  return (
    <div
      className={clsx(
        styles.container,
        {
          [styles.open]: isOpen,
          [styles.pending]: isDefaultTokensLoading || isSearchTokensLoading,
        },
        styles[size],
        className
      )}
      ref={refContainer}>
      <div className={styles.body} {...getToggleButtonProps()}>
        <input
          type="text"
          placeholder={placeholder}
          className={styles.input}
          {...getInputProps({ ref: inputRef })}
          autoFocus
        />

        <div className={styles.token}>
          {!!currentToken && (
            <TokenAsset
              size={size}
              className={styles.asset}
              symbol={currentToken.symbols}
              network={
                usedChains?.find((chain) => chain.name === currentToken.network) ?? {
                  name: 'UNKN',
                }
              }
              logo={currentToken.logoURI}
              description={currentToken.description}
              isLP={currentToken.marketType === 'lp'}
              amm={currentToken.AMM}
              price={currentToken.priceUSD}
              delta={currentToken.priceUSDChange24h * 100}
              verified={currentToken.verified}
            />
          )}

          {!currentToken && <span className={styles.placeholder}>{placeholder}</span>}
        </div>

        <IconDown className={styles.indicator} />
      </div>

      <DropdownContent
        isOpen={isOpen}
        className={clsx(styles.dropdown, {
          [styles.open]: isOpen,
        })}
        {...getMenuProps({}, { suppressRefError: true })}
        element={refContainer.current}>
        <Show if={!isDefaultTokensLoading && !isSearchTokensLoading && !tokensTableData.length}>
          <StateMessage type="danger" className={styles.message} caption="No tokens found" />
        </Show>

        <Show if={tokensTableData.length}>
          <Table
            className={styles.table}
            data={tokensTableData}
            classNameTBody={styles.tbody}
            classNameTCell={styles.tcell}
            rowHref={rowHref}
            rowKey={(item) => `${item.address}-${item.id}`}
            rowProps={getRowProps}
            rowVars={getRowVars}
            columns={tokenSelectorColumns({
              chains: usedChains,
              size,
              isFetching: isFetching && !tokensTableData.length,
            })}
          />
        </Show>
      </DropdownContent>
    </div>
  )
}
