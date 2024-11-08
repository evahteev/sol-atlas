const YANDEX_METRICA_ID = process.env.NEXT_PUBLIC_YANDEX_METRICA_ID

if (!YANDEX_METRICA_ID) {
  console.error('YANDEX_METRICA_ID is not defined. All events will be skipped')
}
export const trackButtonClick = (category: string, action: string, label?: string) => {
  if (!YANDEX_METRICA_ID) {
    return
  }
  const metricaId = parseInt(YANDEX_METRICA_ID)

  if (typeof window !== 'undefined') {
    if (window.gtag) {
      window.gtag('event', action, {
        event_category: category,
        event_label: label,
      })
    }

    if (window.ym && metricaId) {
      window.ym(metricaId, 'reachGoal', {
        action,
        category,
        label,
      })
    }
  }
}
