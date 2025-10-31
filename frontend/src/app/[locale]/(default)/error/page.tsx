'use client'

import { useRouter, useSearchParams } from 'next/navigation'

import StateMessage from '@/components/composed/StateMessage'
import { DEFAULT_REDIRECT_PATH } from '@/config/settings'

import styles from '../../_assets/error.module.scss'

enum Error {
  Configuration = 'Configuration',
}

const errorMap = {
  [Error.Configuration]: (
    <p>
      There was a problem when trying to authenticate. Please contact us if this error persists.
      Unique error code: <code className="rounded-sm bg-slate-100 p-1 text-xs">Configuration</code>
    </p>
  ),
}

export default function AuthErrorPage() {
  const search = useSearchParams()
  const error = search.get('error') as Error
  const router = useRouter()

  return (
    <StateMessage
      type="danger"
      caption="An unhandled error occurred"
      className={styles.container}
      actions={[
        {
          variant: 'danger',
          onClick: () => router.push(DEFAULT_REDIRECT_PATH),
          className: styles.button,
          caption: 'Try again',
        },
      ]}>
      {errorMap[error] || 'Please contact us if this error persists.'}
    </StateMessage>
  )
}
