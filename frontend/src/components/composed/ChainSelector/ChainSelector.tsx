'use client'

import { useRouter } from 'next/navigation'

import { FC, useEffect, useRef, useState } from 'react'

import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { useKey } from 'rooks'
import { UrlObject, format } from 'url'

import ChainAsset from '@/components/atoms/ChainAsset'
import DropdownContent from '@/components/ui/DropdownContent'
import Show from '@/components/ui/Show'
import { TableRowProps } from '@/components/ui/Table/types'
import IconDown from '@/images/icons/chevron-down.svg'
import { ChainModel } from '@/models/chain'

import StateMessage from '../StateMessage'

import styles from './ChainSelector.module.scss'

type ChainSelectorProps = {
  className?: string
  chains?: ChainModel[]
  chain?: ChainModel
  chainHref?: (string | UrlObject | null) | ((chain: ChainModel) => string | UrlObject | null)
  onChainChange?: (chain?: ChainModel) => void
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
}

export const ChainSelector: FC<ChainSelectorProps> = ({
  className,
  chains = [],
  chain,
  chainHref,
  placeholder = 'Search Network',
  onChainChange,
  size = 'md',
}) => {
  const router = useRouter()

  const [currentChain, setCurrentChain] = useState<ChainModel | undefined>(chain ?? chains[0])

  useEffect(() => {
    setCurrentChain(chain ?? chains?.[0])
  }, [chains, chain])

  const [currentQuery, setCurrentQuery] = useState('')

  const refContainer = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (chain?.id === currentChain?.id) {
      return
    }

    setCurrentChain(chain)
  }, [chain, currentChain?.id])

  const currentQueryLowerCase = currentQuery.trim().toLowerCase()

  const chainsFiltered = chains.filter(
    (chain) =>
      `${chain.id}`.includes(currentQueryLowerCase) ||
      chain.name.toLowerCase().includes(currentQueryLowerCase) ||
      chain.description.toLowerCase().includes(currentQueryLowerCase)
  )

  const {
    isOpen,
    openMenu,
    getToggleButtonProps,
    getMenuProps,
    highlightedIndex,
    getItemProps,
    getInputProps,
  } = useCombobox({
    items: chainsFiltered,
    itemToString: () => '',
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem || selectedItem?.id === currentChain?.id) {
        return
      }

      setCurrentChain(selectedItem)
      if (chainHref) {
        router.push(
          format((typeof chainHref === 'function' ? chainHref(selectedItem) : chainHref) ?? '')
        )
      }

      onChainChange?.(selectedItem)
    },
    onInputValueChange: ({ inputValue }) => {
      setCurrentQuery(inputValue)
    },
  })

  useKey(['Backquote', 'IntlBackslash'], () => {
    setTimeout(openMenu, 50)
  })

  const getRowProps = (item?: ChainModel, index?: number): TableRowProps => {
    if (!item) {
      return {}
    }

    return {
      ...getItemProps({ item, index }),
      className: clsx(styles.item, {
        [styles.hilite]: highlightedIndex === index,
      }),
    }
  }

  return (
    <>
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
        <div className={styles.body} {...getToggleButtonProps()}>
          <input
            type="text"
            placeholder={placeholder}
            className={styles.input}
            {...getInputProps({ ref: inputRef })}
            value={currentQuery}
            autoFocus
          />

          <div className={styles.chain}>
            <Show if={currentChain}>
              <ChainAsset
                className={styles.asset}
                logo={currentChain?.logo_uri}
                name={currentChain?.name || 'UNKNOWN'}
                description={currentChain?.description || 'UNKNOWN'}
                size={size}
                color={currentChain?.color}
              />
            </Show>

            <Show if={!currentChain}>
              <span className={styles.placeholder}>{placeholder}</span>
            </Show>
          </div>

          <IconDown className={styles.indicator} />
        </div>
      </div>

      <DropdownContent
        isOpen={isOpen}
        className={clsx(styles.dropdown, {
          [styles.open]: isOpen,
        })}
        {...getMenuProps({}, { suppressRefError: true })}
        element={refContainer.current}>
        <Show if={!chains.length}>
          <StateMessage type="danger" className={styles.message} caption="No chains available" />
        </Show>
        <Show if={isOpen}>
          <ul className={styles.list}>
            {chainsFiltered.map((chain, idx) => (
              <li key={chain.id} {...getRowProps(chain, idx)}>
                <ChainAsset
                  className={styles.asset}
                  logo={chain.logo_uri}
                  name={chain.name || 'UNKNOWN'}
                  description={chain.description || 'UNKNOWN'}
                  size={size}
                  color={chain.color}
                />
              </li>
            ))}
          </ul>
        </Show>
      </DropdownContent>
    </>
  )
}
