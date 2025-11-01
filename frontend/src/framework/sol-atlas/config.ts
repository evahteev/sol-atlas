import { guruNetwork } from '@reown/appkit/networks'
import { env } from 'next-runtime-env'

import { type ApplicationSettings } from '../config'

const ApplicationSettings: ApplicationSettings = {
  DEFAULT_DASHBOARD_NAME: 'dex_guru_tokens',
  LEADERBOARD_DASHBOARD_NAME: 'activity_leaderboard',
  NATIVE_CURRENCY_SYMBOL: guruNetwork.nativeCurrency.symbol,
  pointsToken: {
    id: '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee-gurusepolia',
    address: '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
    name: `${env('NEXT_PUBLIC_POINTS_TOKEN_SYMBOL')}`,
    symbols: [`${env('NEXT_PUBLIC_POINTS_TOKEN_SYMBOL')}`],
    logoURI: [],
    decimals: 18,
    network: 'gurusepolia',
  },
  socials: {
    NEXT_PUBLIC_SOCIAL_TELEGRAM: `${env('NEXT_PUBLIC_SOCIAL_TELEGRAM')}`,
    NEXT_PUBLIC_SOCIAL_X: `${env('NEXT_PUBLIC_SOCIAL_X')}`,
    NEXT_PUBLIC_SOCIAL_DISCORD: `${env('NEXT_PUBLIC_SOCIAL_DISCORD')}`,
    NEXT_PUBLIC_SOCIAL_YOUTUBE: `${env('NEXT_PUBLIC_SOCIAL_YOUTUBE')}`,
  },
}

export { ApplicationSettings }
