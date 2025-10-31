'use client'

import { Tooltip } from 'react-tooltip'

import Show from '@/components/ui/Show'
import { useIsDesktop } from '@/hooks/useIsDesktop'

export default function TooltipProvider() {
  const isDesktop = useIsDesktop()

  return (
    <>
      <Tooltip id="app-tooltip" delayHide={500} />
      <Show if={isDesktop}>
        <Tooltip id="mobile-tooltip" delayHide={500} />
      </Show>
      <Show if={isDesktop}>
        <Tooltip id="desktop-tooltip" delayHide={500} />
      </Show>
    </>
  )
}
