'use client'

import { useEffect } from 'react'

import StateMessage from '@/components/composed/StateMessage'

import styles from './_assets/error.module.scss'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset?: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (
    <StateMessage
      type="danger"
      caption="An unhandled error occurred"
      className={styles.container}
      actions={reset ? [{ caption: 'Try again', onClick: reset, variant: 'danger' }] : undefined}>
      <code className={styles.message}>{error.message}</code>
    </StateMessage>
  )
}
