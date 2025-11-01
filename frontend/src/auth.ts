import { cookies } from 'next/headers'

import jwt from 'jsonwebtoken'
import NextAuth, { Session, User } from 'next-auth'
import { JWT } from 'next-auth/jwt'
import credentialsProvider from 'next-auth/providers/credentials'
import { WalletId } from 'thirdweb/wallets'
import { validate } from 'uuid'

import {
  REF_USER_ID_COOKIE_NAME,
  THIRDWEB_ECOSYSTEM_ID,
  THIRDWEB_JWT_COOKIE_NAME,
} from '@/config/settings'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

declare module 'next-auth' {
  /**
   * The shape of the user object returned in the OAuth providers' `profile` callback,
   * or the second parameter of the `session` callback, when using a database.
   */
  interface User {
    /** Is Admin */
    is_admin: boolean
    /** Is Suspicious */
    is_suspicious: boolean
    /** Camunda User Id */
    camunda_user_id?: string | null
    /** Camunda Key */
    camunda_key?: string | null
    /** Telegram User Id */
    telegram_user_id?: number | null
    /** BloFin User Id */
    blofin_user_id?: string | number | null
    /** Webapp User Id */
    webapp_user_id?: string | null
    /** Is Block */
    is_block: boolean
    /** Language Code */
    language_code?: string | null
    /**
     * Telegram Accounts
     * @default []
     */
    telegram_accounts: components['schemas']['TelegramUserRest'][]
    /**
     * Web3 Wallets
     * @default []
     */
    web3_wallets: components['schemas']['Web3UserRest'][]
  }

  /**
   * Returned by `useSession`, `auth`, contains information about the active session.
   */
  interface Session {
    /** JWT tokens from FLOW API /login endpoint */
    access_token?: string
    refresh_token?: string
    user?: Partial<User>
  }
}

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    /** JWT tokens from FLOW API /login endpoint */
    access_token?: string
    refresh_token?: string
    user?: User
  }
}
export type DecodedFlowApiAccessJWT = {
  sub: string
  iat: number
  nbf: number
  jti: string
  exp: number
  type: 'access' | 'refresh' // Assuming it can be "access" or "refresh"
  fresh: boolean
  id: string
  is_admin: boolean
  is_suspicious: boolean
  is_block: boolean
  is_premium: boolean
  webapp_user_id: string
  username: string
  first_name: string
  last_name: string
  language_code: string
  camunda_user_id: string
  camunda_key: string
  telegram_user_id: number
  discord_user_id: string | null
}

export type DecodedFlowApiRefreshToken = {
  sub: string
  iat: number
  nbf: number
  jti: string
  exp: number
  type: 'refresh'
  id: string
  is_admin: boolean
  is_suspicious: boolean
  is_block: boolean
  is_premium: boolean
  webapp_user_id: string
  username: string
  first_name: string
  last_name: string
  language_code: string
  camunda_user_id: string
  camunda_key: string
  telegram_user_id: number
  discord_user_id: string | null
}

const userHasWallet = (
  user: { web3_wallets: { wallet_address: string }[] },
  wallet_address: string
): boolean => {
  return user?.web3_wallets?.some(
    (x) => x.wallet_address.toLowerCase() === wallet_address.toLowerCase()
  )
}

async function authorizeWithThirdweb(credentials: {
  jwt: string
  wallets: { id: WalletId; address?: string }[]
}) {
  if (!process.env.AUTHJWT_SECRET_KEY) {
    throw new Error('AUTHJWT_SECRET_KEY is not defined for auth')
  }

  const decodedJWT = jwt.verify(credentials.jwt, process.env.AUTHJWT_SECRET_KEY, {
    algorithms: ['HS256'],
  }) as jwt.JwtPayload

  const webAppUserId = decodedJWT.storedToken.authDetails.userWalletId
  const authProvider = decodedJWT.storedToken.authProvider
  const decodedProviderJWT = jwt.decode(decodedJWT.storedToken.jwtToken) as jwt.JwtPayload

  const cookieStore = await cookies()
  const refUserId = cookieStore.get(REF_USER_ID_COOKIE_NAME)?.value

  const upsertWallets = async (user: {
    ref_user_id?: string | null
    web3_wallets: {
      wallet_address: string
    }[]
  }) => {
    if (refUserId && !user.ref_user_id) {
      // @ts-expect-error network_type is not nullable in types
      await FlowClientObject.user.update({
        webapp_user_id: webAppUserId,
        ref_user_id: refUserId,
      })
    }
    await Promise.all(
      credentials.wallets.map(async (wallet) => {
        const address = wallet.address
        if (!address || userHasWallet(user, address)) {
          return
        }

        await FlowClientObject.user.update({
          webapp_user_id: webAppUserId,
          wallet_address: address,
          network_type:
            wallet.id === THIRDWEB_ECOSYSTEM_ID ? 'thirdweb_ecosystem' : `thirdweb_${wallet.id}`,
        })
      })
    )
  }

  try {
    const user = await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
    await upsertWallets(user)
    return await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
  } catch (authError) {
    if (!(authError instanceof Error) || !authError.message.includes('User not found')) {
      throw new Error(`Error getting user data from thirdweb: ${JSON.stringify(authError)}`)
    }

    try {
      if (authProvider === 'Telegram' && decodedProviderJWT.sub) {
        const telegram_user_id = decodedProviderJWT.sub

        const user = await FlowClientObject.user.get({ telegram_user_id }).catch(async () => {
          // @ts-expect-error types
          const newUser = await FlowClientObject.user.create({
            telegram_user_id: parseInt(telegram_user_id),
            username: decodedProviderJWT.username,
            first_name: decodedProviderJWT.firstName,
            last_name: decodedProviderJWT.lastName,
            webapp_user_id: webAppUserId,
            is_block: true,
            ref_user_id: validate(refUserId) ? refUserId : undefined,
          })
          return newUser
        })
        // @ts-expect-error types
        await FlowClientObject.user.update({
          telegram_user_id: parseInt(telegram_user_id),
          webapp_user_id: webAppUserId,
        })

        await upsertWallets(user)
        return await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
      }

      // Fallback for non-Telegram users
      // @ts-expect-error types
      const newUser = await FlowClientObject.user.create({
        webapp_user_id: webAppUserId,
        is_block: true,
        ref_user_id: validate(refUserId) ? refUserId : undefined,
      })
      await upsertWallets(newUser)

      return await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
    } catch (e) {
      console.error("Can't create user with thirdweb", e)
      throw e
    }
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    credentialsProvider({
      name: 'telegram-mini-app',
      credentials: {
        jwt: {
          label: 'Thirdweb JWT',
          type: 'text',
          placeholder: '0x0',
        },
        wallets: {
          label: 'Thirdweb Wallets',
          type: 'text',
          placeholder: '0x0',
        },
      },
      // @ts-expect-error types
      async authorize(credentials: {
        jwt: string
        wallets: {
          id: WalletId
          address?: string
        }[]
      }) {
        let user = null
        try {
          if (credentials?.jwt && credentials?.wallets) {
            credentials.wallets = JSON.parse(credentials.wallets as unknown as string) as {
              id: WalletId
              address?: string
            }[]
            const user = await authorizeWithThirdweb(credentials)

            const cookieStore = await cookies()
            cookieStore.set(THIRDWEB_JWT_COOKIE_NAME, credentials.jwt, {
              httpOnly: true,
              secure: true,
            })
            return user
          }

          return user
        } catch (authorizeError) {
          console.error(`authorizeError: ${JSON.stringify(authorizeError)}`)
          signOut({ redirect: false })

          user = null
        }

        return user
      },
    }),
  ],
  trustHost: true,
  session: {
    strategy: 'jwt',
    maxAge: 60 * 60 * 24, // 24h
    updateAge: 60 * 10, // 10min
  },
  callbacks: {
    async redirect({ url, baseUrl }) {
      // Allow callback URLs that are relative paths
      if (url.startsWith('/')) {
        return `${baseUrl}${url}`
      }
      // Allow callback URLs from the same origin
      if (url.startsWith(baseUrl)) {
        return url
      }
      // Default to base URL for external URLs (security)
      return baseUrl
    },
    async jwt({ token, user }) {
      if (user) {
        const {
          id,
          is_admin,
          is_block,
          web3_wallets,
          webapp_user_id,
          telegram_user_id,
          camunda_user_id,
          language_code,
        } = user

        token.user = {
          id,
          is_admin,
          is_block,
          web3_wallets,
          webapp_user_id,
          telegram_user_id,
          camunda_user_id,
          language_code,
        } as User
      }

      return token
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (!token) {
        return session
      }
      const {
        id,
        is_admin,
        is_block,
        web3_wallets,
        webapp_user_id,
        telegram_user_id,
        camunda_user_id,
        language_code,
      } = token.user as User
      session.user = {
        id,
        is_admin,
        is_block,
        web3_wallets,
        webapp_user_id,
        telegram_user_id,
        camunda_user_id,
        language_code,
      }

      if (session?.user?.is_block) {
        // eagerly lookup user data from flowapi until they are blocked
        const dbUser = await FlowClientObject.user.get({ user_id: session.user.id })
        const {
          id,
          is_admin,
          is_block,
          web3_wallets,
          webapp_user_id,
          telegram_user_id,
          camunda_user_id,
          language_code,
        } = dbUser
        session.user = {
          id,
          is_admin,
          is_block,
          web3_wallets,
          webapp_user_id,
          telegram_user_id,
          camunda_user_id,
          language_code,
        }
        session.expires = new Date().toISOString()
        if (token?.user)
          token.user = {
            id,
            is_admin,
            is_block,
            web3_wallets,
            webapp_user_id,
            telegram_user_id,
            camunda_user_id,
            language_code,
          } as User
      }

      if (!session?.access_token) {
        const userId = session?.user?.webapp_user_id
        if (!userId) {
          console.warn('[JWT] Missing userId — cannot set access_token')
          return session
        }

        const cookieStore = await cookies()

        // TEMP: delete old large auth cookies. safe to remove it after 30 days
        if (cookieStore.has('authjs.session-token.0')) {
          cookieStore.delete('authjs.session-token.0')
          cookieStore.delete('authjs.session-token.1')
        }

        const access_token = cookieStore.get(THIRDWEB_JWT_COOKIE_NAME)?.value

        if (access_token) {
          session.access_token = access_token
        } else {
          throw new Error(`[JWT] No access token cookie found for userId: ${userId}`)
        }
      }

      return session
    },
  },
  pages: {
    error: '/login',
    signIn: '/login',
  },
  debug: process.env.NODE_ENV !== 'production' ? true : false,
})

export default auth
