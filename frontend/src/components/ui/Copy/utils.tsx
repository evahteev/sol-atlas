import { toast } from 'react-toastify'

import IconCopy from '@/images/icons/copy.svg'

import styles from './Copy.module.scss'

export const doCopyToClipboard = (text: string) => {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      toast.success('Copied to Clipboard!', {
        toastId: 'clipboard-toast',
        icon: <IconCopy className={styles.success} />,
      })
    })
    .catch(() => {
      toast.error('Text copy failed!', {
        toastId: 'clipboard-toast',
      })
    })
}
