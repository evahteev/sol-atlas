import StateMessage from '@/components/composed/StateMessage'

import styles from './_assets/error.module.scss'

export default function NotFound() {
  return (
    <StateMessage
      type="danger"
      caption="Resource Not Found"
      text="We couldn't find this URL"
      className={styles.container}
      actions={[{ caption: 'Reload Page', className: styles.button, href: '/' }]}
    />
  )
}
