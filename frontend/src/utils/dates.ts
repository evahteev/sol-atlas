import { UTCDate } from '@date-fns/utc'
import { endOfDay } from 'date-fns/endOfDay'
import { endOfMonth } from 'date-fns/endOfMonth'
import { endOfWeek } from 'date-fns/endOfWeek'
import { endOfYear } from 'date-fns/endOfYear'
import { format } from 'date-fns/format'
import { startOfDay } from 'date-fns/startOfDay'
import { startOfMonth } from 'date-fns/startOfMonth'
import { startOfWeek } from 'date-fns/startOfWeek'
import { startOfYear } from 'date-fns/startOfYear'
import { subDays } from 'date-fns/subDays'
import { subMonths } from 'date-fns/subMonths'
import { subWeeks } from 'date-fns/subWeeks'
import { subYears } from 'date-fns/subYears'

export type DateTimeRangeFormat = 'date-range' | 'datetime-range' | 'datetime-range-with-seconds'

export const DYNAMIC_DATE_PREFIX = 'd_'
export const DEFAULT_DATE_RANGE = 'last_14_days'
export const DATETIME_FORMATS: Record<DateTimeRangeFormat, string> = {
  'date-range': 'yyyy-MM-dd',
  'datetime-range': 'yyyy-MM-dd HH:mm',
  'datetime-range-with-seconds': 'yyyy-MM-dd HH:mm:ss',
}

export const getDynamicDateRangePeriod = (
  value: string,
  type: DateTimeRangeFormat = 'date-range'
): { start: string | null; end: string | null } | null => {
  const re = new RegExp(`^${DYNAMIC_DATE_PREFIX}(.+)$`, 'i')
  const possibleDynamicDateRange = value.toLowerCase().match(re)?.[1]
  const range = DYNAMIC_DATE_RANGES[possibleDynamicDateRange || DEFAULT_DATE_RANGE]?.value()

  return range
    ? {
        start: getFormattedDate(range?.start, type) || null,
        end: getFormattedDate(range?.end, type) || null,
      }
    : null
}

const getFormattedDate = (
  moment = new UTCDate(),
  dateTimeType: DateTimeRangeFormat = 'date-range'
): string => {
  return format(moment, DATETIME_FORMATS[dateTimeType])
}

export const DYNAMIC_DATE_RANGES: Record<
  string,
  { name: string; value: () => { start: UTCDate; end: UTCDate } }
> = {
  today: {
    name: 'Today',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(moment),
        end: endOfDay(moment),
      }
    },
  },
  yesterday: {
    name: 'Yesterday',
    value: () => {
      const moment = subDays(new UTCDate(), 1)

      return {
        start: startOfDay(moment),
        end: endOfDay(moment),
      }
    },
  },
  this_week: {
    name: 'This week',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfWeek(moment),
        end: endOfWeek(moment),
      }
    },
  },
  this_month: {
    name: 'This month',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfMonth(moment),
        end: endOfMonth(moment),
      }
    },
  },
  this_year: {
    name: 'This year',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfYear(moment),
        end: endOfYear(moment),
      }
    },
  },
  last_week: {
    name: 'Last week',
    value: () => {
      const moment = subWeeks(new UTCDate(), 1)

      return {
        start: startOfWeek(moment),
        end: endOfWeek(moment),
      }
    },
  },
  last_month: {
    name: 'Last month',
    value: () => {
      const moment = subMonths(new UTCDate(), 1)

      return {
        start: startOfMonth(moment),
        end: endOfMonth(moment),
      }
    },
  },
  last_year: {
    name: 'Last year',
    value: () => {
      const moment = subYears(new UTCDate(), 1)

      return {
        start: startOfYear(moment),
        end: endOfYear(moment),
      }
    },
  },
  // last_hour: {
  //   name: 'Last hour',
  //   value: () => {
  //     const moment = subHours(new UTCDate(), 1)

  //     return {
  //       start: startOfHour(moment)),
  //       end: endOfHour(moment)),
  //     }
  //   },
  // },
  // last_8_hours: {
  //   name: 'Last 8 hours',
  //   value: () => {
  //     const moment = new UTCDate()

  //     return {
  //       start: subHours(moment, 1)),
  //       end: endOfHour(moment)),
  //     }
  //   },
  // },
  // last_24_hours: {
  //   name: 'Last 24 hours',
  //   value: () => {
  //     const moment = new UTCDate()

  //     return {
  //       start: subMinutes(moment, 60)),
  //       end: moment),
  //     }
  //   },
  // },
  last_7_days: {
    name: 'Last 7 days',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subDays(moment, 7)),
        end: endOfDay(moment),
      }
    },
  },
  last_14_days: {
    name: 'Last 14 days',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subDays(moment, 14)),
        end: endOfDay(moment),
      }
    },
  },
  last_30_days: {
    name: 'Last 30 days',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subDays(moment, 30)),
        end: endOfDay(moment),
      }
    },
  },
  last_60_days: {
    name: 'Last 60 days',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subDays(moment, 60)),
        end: endOfDay(moment),
      }
    },
  },
  last_90_days: {
    name: 'Last 90 days',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subDays(moment, 90)),
        end: endOfDay(moment),
      }
    },
  },
  last_12_months: {
    name: 'Last 12 months',
    value: () => {
      const moment = new UTCDate()

      return {
        start: startOfDay(subMonths(moment, 12)),
        end: endOfDay(moment),
      }
    },
  },
}

export const getDateTime = (
  time: number | string | UTCDate,
  options?: Intl.DateTimeFormatOptions
): string => {
  const date = new UTCDate(time)
  return date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    weekday: 'short',
    hour12: false,
    ...(options ?? {}),
  })
}

export const getDate = (
  time: number | string | UTCDate,
  options?: Intl.DateTimeFormatOptions
): string => {
  const date = new UTCDate(time)
  return date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour12: false,
    ...(options ?? {}),
  })
}

export const getTime = (
  time: number | string | UTCDate,
  options?: Intl.DateTimeFormatOptions
): string => {
  const date = new UTCDate(time)
  return date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    ...(options ?? {}),
  })
}

export const getShortDate = (
  time: number | string | UTCDate,
  options?: Intl.DateTimeFormatOptions
) => {
  const date = new UTCDate(time)
  return date
    .toLocaleDateString('en-GB', {
      timeZone: 'UTC',
      month: 'short',
      year: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      ...(options ?? {}),
    })
    .replace(/:00$/, '')
    .replace(', 00:00', '')
}

export const convertTimespan = (
  value: number,
  timespanFrom: string,
  timespanTo: string = 'second'
): number => {
  const unitToSeconds: Record<string, number> = {
    second: 1,
    minute: 60,
    hour: 60 * 60,
    day: 24 * 60 * 60,
    week: 7 * 24 * 60 * 60,
    month: 30 * 24 * 60 * 60,
    year: 365 * 24 * 60 * 60,
  }

  return Math.floor(
    (value * (unitToSeconds[timespanFrom] ?? 'second')) / (unitToSeconds[timespanTo] ?? 'second')
  )
}
