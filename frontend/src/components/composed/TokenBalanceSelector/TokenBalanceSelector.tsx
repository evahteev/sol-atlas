'use client'

import { useRouter } from 'next/navigation'

import { FC, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { useKey } from 'rooks'
import { UrlObject, format } from 'url'

import TokenAsset from '@/components/atoms/TokenAsset'
import Value from '@/components/atoms/Value'
import DropdownContent from '@/components/ui/DropdownContent'
import Show from '@/components/ui/Show'
import { Table } from '@/components/ui/Table/Table'
import { TableRowProps } from '@/components/ui/Table/types'
import { useWalletTotals } from '@/hooks/useWalletTotals'
import IconSearch from '@/images/icons/search.svg'
import { TokenV3Model, TokenV3ModelWithBalances } from '@/models/token'
import { AppContext } from '@/providers/context'
import { formatNumber } from '@/utils/numbers'
import { getBalanceFromList, getTokenSymbolsString } from '@/utils/tokens'

import StateMessage from '../StateMessage'
import { tokenBalanceColumns } from './columns'

import styles from './TokenBalanceSelector.module.scss'

type TokenBalanceSelectorProps = {
  className?: string
  token?: TokenV3ModelWithBalances
  account?: string
  rowHref?:
    | (string | UrlObject | null)
    | ((token?: TokenV3Model, idx?: number) => string | UrlObject | null)
  onTokenChange?: (token?: TokenV3ModelWithBalances) => void
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
}

export const TokenBalanceSelector: FC<TokenBalanceSelectorProps> = ({
  className,
  token,
  account,
  rowHref,
  placeholder = 'Search token by address or ticker',
  onTokenChange,
  size = 'lg',
}) => {
  const { chains } = useContext(AppContext)

  const router = useRouter()

  const [currentToken, setCurrentToken] = useState<TokenV3ModelWithBalances | undefined>(token)
  const [currentQuery, setCurrentQuery] = useState('')

  const { tokens, natives, isFetching } = useWalletTotals({
    address: account || '',
    chains,
    refetchInterval: 5 * 60 * 1000,
  })
  const balances = useMemo(() => [...tokens, ...natives], [natives, tokens])

  const refContainer = useRef<HTMLDivElement>(null)

  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setCurrentToken(token)
  }, [token])

  const balancesFiltered: TokenV3ModelWithBalances[] = balances
    .filter(
      (balance) =>
        !currentQuery ||
        balance.id.toLocaleLowerCase().includes(currentQuery) ||
        balance.address.toLocaleLowerCase().includes(currentQuery) ||
        balance.network.toLocaleLowerCase().includes(currentQuery) ||
        balance.name.toLocaleLowerCase().includes(currentQuery) ||
        balance.symbols.join('/').toLocaleLowerCase().includes(currentQuery) ||
        balance.description.toLocaleLowerCase().includes(currentQuery)
    )
    .sort(
      (a, b) =>
        Number(b.verified) - Number(a.verified) || b.balance * b.priceUSD - a.balance * a.priceUSD
    ) // sort first by verified field, then by $value

  const {
    isOpen,
    openMenu,
    getToggleButtonProps,
    getMenuProps,
    highlightedIndex,
    getItemProps,
    getInputProps,
  } = useCombobox({
    items: balancesFiltered,
    itemToString: (item) => getTokenSymbolsString(item?.token_symbol || ''),
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem) {
        return
      }

      setCurrentToken(selectedItem)
      if (rowHref) {
        router.push(format((typeof rowHref === 'function' ? rowHref(selectedItem) : rowHref) ?? ''))
      }
      onTokenChange?.(selectedItem)
    },
    onInputValueChange: ({ inputValue }) => {
      setCurrentQuery(inputValue.trim().toLocaleLowerCase())
    },
  })

  useKey(['Backquote', 'IntlBackslash'], () => {
    setTimeout(openMenu, 50)
  })

  const getRowProps = (item?: TokenV3ModelWithBalances, index?: number): TableRowProps => {
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
    (item?: TokenV3ModelWithBalances): TableRowProps => {
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
        },
        styles[size],
        className
      )}
      ref={refContainer}>
      <div className={styles.body}>
        <input
          type="text"
          placeholder={placeholder}
          className={styles.input}
          {...getInputProps({ ref: inputRef })}
          autoFocus
        />

        <div className={styles.token} {...getToggleButtonProps()}>
          {!!currentToken && (
            <>
              <TokenAsset
                size={size}
                className={styles.asset}
                symbol={currentToken.token_symbol}
                network={
                  chains?.find((chain) => chain.name === currentToken.network) ?? { name: 'UNKN' }
                }
                logo={currentToken.logoURI}
                description={currentToken.description}
                isLP={currentToken.marketType === 'lp'}
                amm={currentToken.AMM}
                price={currentToken.priceUSD}
                delta={currentToken.priceUSDChange24h * 100}
              />
              <Show if={account}>
                <Value
                  value={formatNumber(getBalanceFromList(balances, currentToken))}
                  className={styles.price}
                  prefix={<>Balance&nbsp;</>}
                />
              </Show>
            </>
          )}

          <IconSearch className={styles.search} />

          {!currentToken && <span className={styles.placeholder}>{placeholder}</span>}
        </div>
      </div>

      <DropdownContent
        isOpen={isOpen}
        className={clsx(styles.dropdown, {
          [styles.open]: isOpen,
        })}
        {...getMenuProps({}, { suppressRefError: true })}
        element={refContainer.current}>
        <Show if={!balances.length}>
          <StateMessage type="danger" className={styles.message} caption="No balances found" />
        </Show>

        <Show if={balances.length}>
          <Table
            className={styles.table}
            data={balancesFiltered}
            classNameTBody={styles.tbody}
            classNameTCell={styles.tcell}
            rowHref={rowHref}
            rowKey={(item) => `${item.token_address}-${item.id}`}
            rowProps={getRowProps}
            rowVars={getRowVars}
            columns={tokenBalanceColumns({
              chains,
              size,
              isFetching: isFetching && !balances.length,
            })}
          />
        </Show>
      </DropdownContent>
    </div>
  )
}
