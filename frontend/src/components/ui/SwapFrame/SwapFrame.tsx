'use client'

import { FC, useCallback, useEffect, useRef, useState } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'
import { useBoundingclientrectRef } from 'rooks'

import Tabs from '@/components/composed/Tabs'
import InfoPanel from '@/components/page/InfoPanel'
import { mapGuruNetworkToChainId, mapNetwork } from '@/utils/chains'

import Message from '../Message'
import {
  SWAP_PROVIDERS,
  SwapProvider,
  debridgeContainerId,
  debridgeRefCode,
  disabledProviders,
  feeAddressReceiver,
  integrator,
  jupiterContainerId,
  jupiterReferralPubKey,
  solRPC,
} from './settings'

import styles from './SwapFrame.module.scss'

type TokenMinimal = { address: string; network: string }

export type SwapFrameProps = {
  className?: string
  tokenIn?: TokenMinimal
  tokenOut?: TokenMinimal
  amountIn?: string
  isSelectable?: boolean
  initialProvider?: SwapProvider
}
const getUrl = (
  provider: SwapProvider,
  tokenIn?: TokenMinimal,
  tokenOut?: TokenMinimal,
  amountIn?: string
): string => {
  const partnerSearchParams: Record<SwapProvider, URLSearchParams> = {
    bridge: new URLSearchParams(),
    guruswap: new URLSearchParams(),
    paraswap: new URLSearchParams({
      partnerAddress: feeAddressReceiver,
      partner: integrator,
      partnerFeeBps: '100',
      takeSurplus: 'true',
    }),
    bebop: new URLSearchParams({
      source: integrator,
    }),
    kyberswap: new URLSearchParams({
      clientId: integrator,
      feeReceiver: feeAddressReceiver,
      chargeFeeBy: 'currency_in',
      feeAmount: '100',
      isInBps: 'true',
    }),
    debridge: new URLSearchParams(),
    jupiter: new URLSearchParams(),
  }

  if (!tokenOut) {
    const baseUrl: Record<SwapProvider, string> = {
      bridge: 'https://bridge.gurunetwork.ai',
      guruswap: 'https://swap.gurunetwork.ai',
      paraswap: `https://embedded.paraswap.io`,
      bebop: `https://bebop.xyz/trade`,
      kyberswap: `https://kyberswap.com/partner-swap`,
      debridge: `https://app.debridge.finance/widget`,
      jupiter: '',
    }
    return provider === 'paraswap'
      ? `${baseUrl[provider]}/?${partnerSearchParams[provider]}#/swap`
      : `${baseUrl[provider]}?${partnerSearchParams[provider]}`
  }

  const tokenInAddress = tokenIn?.address ?? '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
  const swapSearchParams: Record<SwapProvider, URLSearchParams> = {
    bridge: new URLSearchParams(),
    guruswap: new URLSearchParams(),
    paraswap: new URLSearchParams({ network: mapNetwork(tokenOut.network, 'paraswap') }),
    bebop: new URLSearchParams({
      network: mapNetwork(tokenOut.network, 'bebop'),
      buy: tokenOut.address,
      sellAmounts: amountIn ?? '1',
      sell: tokenInAddress,
    }),
    kyberswap: new URLSearchParams({
      chainId: `${mapGuruNetworkToChainId[tokenOut.network]}`,
      amountOut: amountIn ?? '1',
      inputCurrency: tokenInAddress,
      outputCurrency: tokenOut.address,
    }),
    debridge: new URLSearchParams(),
    jupiter: new URLSearchParams(),
  }
  const baseUrl: Record<SwapProvider, string> = {
    bridge: 'https://bridge.gurunetwork.ai',
    guruswap: 'https://swap.gurunetwork.ai',
    paraswap: `https://embedded.paraswap.io`,
    bebop: `https://bebop.xyz/trade`,
    kyberswap: `https://kyberswap.com/partner-swap`,
    debridge: `https://app.debridge.finance/widget`,
    jupiter: '',
  }
  return provider === 'paraswap'
    ? `${baseUrl[provider]}/?${partnerSearchParams[provider]}#/swap/${tokenInAddress}-${tokenOut.address}/${amountIn ?? 1}/SELL&${swapSearchParams[provider]}`
    : `${baseUrl[provider]}?${partnerSearchParams[provider]}&${swapSearchParams[provider]}`
}
const getTips = (provider: SwapProvider, t: (key: string) => string): string | null => {
  const tips: Record<SwapProvider, string> = {
    paraswap: t('tips.paraswap'),
    bebop: '',
    bridge: '',
    guruswap: t('tips.guruswap'),
    kyberswap: t('tips.kyberswap'),
    debridge: t('tips.debridge'),
    jupiter: t('tips.jupiter'),
  }

  return tips[provider] ? `${t('tips.prefix')}${tips[provider]}` : null
}

export const SwapFrame: FC<SwapFrameProps> = ({
  tokenIn,
  tokenOut,
  amountIn,
  isSelectable = false,
  initialProvider = 'debridge',
}) => {
  const t = useTranslations('Swap')
  const [provider, setProvider] = useState<SwapProvider>(initialProvider)

  const [containerRef, boundingClientRect] = useBoundingclientrectRef()
  const debridgeWidget = useRef<DebridgeWidget | undefined>(undefined)

  const initDeBridge = useCallback(() => {
    if (!boundingClientRect?.width) {
      return
    }
    const inputChain = tokenIn?.network ?? tokenOut?.network ?? 'solana'
    const outputChain = tokenOut?.network ?? 'solana'

    window.deBridge
      .widget({
        element: debridgeContainerId,
        width: boundingClientRect?.width ?? 0,
        v: '1',
        r: debridgeRefCode, // ref code for debridge
        affiliateFeePercent: '1',
        affiliateFeeRecipient: feeAddressReceiver, // EVM swaps
        affiliateFeePercentSolana: '1',
        affiliateFeeRecipientSolana: jupiterReferralPubKey, // SOL swaps
        supportedChains:
          '{"inputChains":{"1":"all","10":"all","56":"all","100":"all","137":"all","146":"all","250":"all","388":"all","998":"all","1088":"all","1514":"all","2741":"all","4158":"all","7171":"all","8453":"all","42161":"all","43114":"all","59144":"all","80094":"all","7565164":"all","245022934":"all"},"outputChains":{"1":"all","10":"all","56":"all","100":"all","137":"all","146":"all","250":"all","388":"all","998":"all","1088":"all","1514":"all","2741":"all","4158":"all","7171":"all","8453":"all","42161":"all","43114":"all","59144":"all","80094":"all","7565164":"all","245022934":"all"}}',
        disabledWallets: [
          'Trust Wallet',
          'ONEINCHWALLET',
          'Fordefi',
          'RABBY',
          'UNSTOPPABLEDOMAINS',
          'Frontier',
          'GNOSIS',
          'Trust',
          'Fordefi Solana',
          'Glow',
        ],
        inputChain: mapGuruNetworkToChainId[inputChain],
        outputChain: mapGuruNetworkToChainId[outputChain],
        inputCurrency: tokenIn?.address ?? '',
        outputCurrency: tokenOut?.address ?? '',
        showSwapTransfer: true,
        amount: amountIn ?? '',
        outputAmount: '',
        theme: 'dark',
        isHideLogo: true,
      })
      .then((widget) => {
        debridgeWidget.current = widget
      })
  }, [
    amountIn,
    boundingClientRect?.width,
    tokenIn?.address,
    tokenIn?.network,
    tokenOut?.address,
    tokenOut?.network,
  ])

  useEffect(() => {
    if (provider === 'jupiter') {
      const widgetContainer = document.getElementById(jupiterContainerId)

      // Ensure the container exists
      if (!widgetContainer) {
        console.error(`Element with ID ${jupiterContainerId} not found.`)
        return
      }

      const script = document.createElement('script')
      script.src = 'https://terminal.jup.ag/main-v3.js'
      script.async = true
      script.dataset.preload = ''
      script.onload = () => {
        const config = {
          displayMode: 'integrated' as const,
          integratedTargetId: jupiterContainerId, // The container ID for standard DOM
          endpoint: solRPC,
          defaultExplorer: 'Solscan' as const,
          enableWalletPassthrough: false,
          platformFeeAndAccounts: {
            feeBps: 100,
            referralAccount: jupiterReferralPubKey,
          },
        }

        // Initialize Jupiter Terminal
        window.Jupiter.init(config)
      }

      // Append script to the document body
      document.body.appendChild(script)

      return () => {
        if (provider !== 'jupiter') {
          document.body.removeChild(script) // Cleanup script on unmount
        }
      }
    } //  mount only once
  }, [provider])

  useEffect(() => {
    if (provider === 'debridge' && !debridgeWidget.current) {
      const script = document.createElement('script')
      script.src = 'https://app.debridge.finance/assets/scripts/widget.js'
      script.async = true
      script.onload = () => {
        // Initialize the Debridge widget on the #debridge-widget-container element
        // Refer to the Debridge documentation to set options as needed
        // if tokens aren't defined or solana then fallback to jupiter ref
        initDeBridge()
      }
      document.body.appendChild(script)

      // Cleanup the script when provider changes or component unmounts
      return () => {
        document.body.removeChild(script)
      }
    }
  }, [initDeBridge, provider])

  useEffect(() => {
    if (provider !== 'debridge' && debridgeWidget.current) {
      const iFrameElement = debridgeWidget.current.getFrame()
      document.getElementById(debridgeContainerId)?.removeChild(iFrameElement)
      debridgeWidget.current = undefined
    }
  }, [provider])

  const tipsMessage = getTips(provider, t)
  return (
    <div className={styles.container}>
      {tipsMessage && (
        <InfoPanel className={styles.header}>
          <Message type="info" className={styles.message}>
            {tipsMessage}
          </Message>
        </InfoPanel>
      )}
      <div className={styles.body} ref={containerRef}>
        {provider === 'debridge' && <div id={debridgeContainerId} className={styles.frame} />}
        {provider === 'jupiter' && (
          <div id={jupiterContainerId} className={clsx(styles.frame, styles.jupiter)} />
        )}
        {!['debridge', 'jupiter'].includes(provider) && (
          <iframe className={styles.frame} src={getUrl(provider, tokenIn, tokenOut, amountIn)} />
        )}
      </div>
      {isSelectable && (
        <div className={styles.footer}>
          <Tabs
            className={styles.tabs}
            tabs={SWAP_PROVIDERS.filter((x) => !disabledProviders.includes(x)).map((prov) => ({
              isActive: prov === provider,
              onClick: () => setProvider(prov),
              caption: prov,
            }))}
          />
        </div>
      )}
    </div>
  )
}
