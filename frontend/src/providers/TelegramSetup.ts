import { $debug, init, miniApp, swipeBehavior, viewport } from '@telegram-apps/sdk'
import { RGB, requestWriteAccess } from '@telegram-apps/sdk-react'

import styles from '@/app/_assets/layout.module.scss'

export const TelegramSetup = async (debug: boolean): Promise<boolean> => {
  try {
    // Set @telegram-apps/sdk-react debug mode.
    $debug.set(debug)

    // Initialize special event handlers for Telegram Desktop, Android, iOS, etc. Also, configure
    // the package.
    init()

    miniApp.mount()
    await viewport
      .mount()
      .then(() => viewport.expand())
      .catch((e) => {
        console.error('Something went wrong mounting the viewport', e)
      })
    swipeBehavior.mount()

    if (viewport) {
      viewport.expand()
    }
    swipeBehavior.disableVertical()

    if (miniApp.setHeaderColor.isSupported() && miniApp.setHeaderColor.supports('color')) {
      miniApp.setHeaderColor(styles.primaryColor as RGB)
    }

    if (miniApp.setBackgroundColor.isSupported()) {
      miniApp.setBackgroundColor(styles.primaryColor as RGB)
    }

    if (requestWriteAccess.isSupported()) {
      const status = await requestWriteAccess()
      console.log('requestWriteAccess', status)
    }
  } catch (e) {
    console.error(e)
    return false
  }

  return true
}
