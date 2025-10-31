/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  type DebridgeWidgetEventParams = { address: string; chainId: number }
  type DebridgeWidget = {
    on: (
      e: string,
      callback: (event: DebridgeWidget, params: DebridgeWidgetEventParams) => void
    ) => void
    off: (
      e: string,
      callback: (event: DebridgeWidget, params: DebridgeWidgetEventParams) => void
    ) => void
    getWidgetId: () => number
    getOrigin: () => string
    getParentURI: () => string
    getFrame: () => HTMLIFrameElement
  }
  interface Window {
    gtag: (...args: any[]) => void
    ym: (id: number, command: string, options?: Record<string, any>) => void
    deBridge: {
      widget: (props: {
        element: string // "debridgeWidget",
        v: string // ‘1’,
        mode: string // ‘deswap’,
        title?: string // "deSwap",
        width?: number // "600",
        height?: number // "800",
        inputChain: number // "56",
        outputChain: number // "1",
        disabledWallets: string[] // ["Trust Wallet","ONEINCHWALLET","Fordefi","RABBY","UNSTOPPABLEDOMAINS","Frontier","GNOSIS","Trust","Fordefi Solana","Glow"]
        supportedChains?: string // "supportedChains":"{\"inputChains\":{\"7565164\":\"all\"},\"outputChains\":{\"7565164\":\"all\"}}"
        inputCurrency: string // "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
        outputCurrency: string // "0xdac17f958d2ee523a2206206994597c13d831ec7",
        address?: string // "0x64023dEcf09f20bA403305F5A2946b5b33d1933B",
        amount: string // "10",
        lang?: string // "en",
        mode?: string // "deswap",
        styles?: string // "eyJmb250RmFtaWx5IjoiQWJlbCJ9",
        theme: string //  "dark",
        r: string // ‘3981’
        affiliateFeePercent: string // '1',
        affiliateFeeRecipient: string //feeAddressReceiver,
        affiliateFeePercentSolana: string // '1',
        affiliateFeeRecipientSolana: string //feeAddressReceiver,
        showSwapTransfer: boolean // true,
        outputAmount: string // '',
        isHideLogo: boolean
      }) => Promise<DebridgeWidget>
    }
  }
}

export {}
