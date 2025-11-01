import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'

type ApplicationSettings = {
  DEFAULT_DASHBOARD_NAME: string
  LEADERBOARD_DASHBOARD_NAME: string
  NATIVE_CURRENCY_SYMBOL: string
  pointsToken: CustomToken
  staking?: {
    token: CustomToken
    rewardToken: CustomToken
  }
  socials?: {
    NEXT_PUBLIC_SOCIAL_TELEGRAM: string
    NEXT_PUBLIC_SOCIAL_X: string
    NEXT_PUBLIC_SOCIAL_DISCORD: string
    NEXT_PUBLIC_SOCIAL_YOUTUBE: string
  }
}

export { type ApplicationSettings }
