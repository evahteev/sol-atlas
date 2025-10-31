import { GoogleAnalytics, GoogleTagManager } from '@next/third-parties/google'

const GA_TRACKING_ID = process.env.GA_TRACKING_ID

export default function AnalyticsProvider() {
  if (!GA_TRACKING_ID) {
    return null
  }
  return (
    <>
      <GoogleTagManager gtmId={GA_TRACKING_ID} />
      <GoogleAnalytics gaId={GA_TRACKING_ID} />
    </>
  )
}
