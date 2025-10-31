import { env } from 'next-runtime-env'

// import { Environment, EnvironmentSettings } from "@/components/feature/LoginEnvironments/loginEnvironments"
export const AUTH_COOKIE_NAME = 'access_token_cookie'
export const AUTH_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
export const REF_USER_ID_COOKIE_NAME = 'gurunetwork_ref_user_id'
export const THIRDWEB_JWT_COOKIE_NAME = 'gurunetwork_thirdweb_jwt'
export const THIRDWEB_ECOSYSTEM_ID = 'ecosystem.guru-network'
export const NATIVE_TOKEN_ADDRESS = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'

export const JWT_TOKEN_REFRESH_INTERVAL = 60 * 60 * 1000 // 1 hour
export enum LocalStorageKeyEnum {
  account_id = 'accountId',
  access_token = 'accessToken',
  refresh_token = 'refreshToken',
}

export const DEXGURU_AUTH_URL = 'https://auth.dex.guru/v3'
export const DEFAULT_REDIRECT_PATH = `${env('NEXT_PUBLIC_DEFAULT_REDIRECT_PATH')}` || '/'
