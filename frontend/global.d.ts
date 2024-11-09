declare global {
  interface Window {
    gtag: (...args: any[]) => void
  }

  interface Window {
    ym: (id: number, command: string, options?: Record<string, any>) => void
  }
}

export {}
