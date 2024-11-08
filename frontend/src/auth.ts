// src/auth.ts
import { getAddressFromMessage, getChainIdFromMessage, verifySignature } from '@reown/appkit-siwe'
import { User as TelegramUserData } from '@telegram-apps/sdk'
import { decode } from 'jsonwebtoken'
import NextAuth, { Session, User } from 'next-auth'
import { JWT } from 'next-auth/jwt'
import credentialsProvider from 'next-auth/providers/credentials'
import { v4 as uuidv4 } from 'uuid'

import { projectId } from '@/config/wagmi'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'
import { transformKeysToSnakeCase } from '@/utils/camelToSnakeCase'

export interface TelegramUserDataSnakeCase {
  /**
   * True, if this user added the bot to the attachment menu.
   */
  added_to_attachment_menu?: boolean
  /**
   * True, if this user allowed the bot to message them.
   */
  allows_write_to_pm?: boolean
  /**
   * First name of the user or bot.
   */
  first_name?: string | null
  /**
   * A unique identifier for the user or bot.
   */
  id?: number
  /**
   * True, if this user is a bot. Returned in the `receiver` field only.
   * @see InitDataParsed.receiver
   */
  is_bot?: boolean
  /**
   * True, if this user is a Telegram Premium user.
   */
  is_premium?: boolean
  /**
   * Last name of the user or bot.
   */
  last_name?: string | null
  /**
   * [IETF language tag](https://en.wikipedia.org/wiki/IETF_language_tag) of the user's language.
   * Returns in user field only.
   */
  language_code?: string | null
  /**
   * URL of the user’s profile photo. The photo can be in .jpeg or .svg
   * formats. Only returned for Mini Apps launched from the attachment menu.
   */
  photo_url?: string
  /**
   * Username of the user or bot.
   */
  username?: string | null
}

declare module 'next-auth' {
  /**
   * The shape of the user object returned in the OAuth providers' `profile` callback,
   * or the second parameter of the `session` callback, when using a database.
   */
  interface User extends TelegramUserDataSnakeCase {
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
    /** Webapp User Id */
    webapp_user_id?: string | null
    /** Is Block */
    is_block: boolean
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
    access_token?: string
    refresh_token?: string
    user: User
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    credentialsProvider({
      name: 'telegram-mini-app',
      credentials: {
        telegram_user: {
          label: 'Telegram User Launch Params',
          type: 'Number',
        },
        message: {
          label: 'Message',
          type: 'text',
          placeholder: '0x0',
        },
        signature: {
          label: 'Signature',
          type: 'text',
          placeholder: '0x0',
        },
      },
      async authorize(credentials) {
        try {
          if (!credentials?.telegram_user) {
            throw new Error('Telegram User is not defined')
          }
          const tgUserData = JSON.parse(credentials.telegram_user as string) as TelegramUserData

          if (!tgUserData?.id) {
            throw new Error('Telegram User ID is not defined')
          }
          const telegram_user_id = tgUserData.id.toString()

          try {
            // get existing user
            const user = await FlowClientObject.user.get(telegram_user_id)
            if (!user.webapp_user_id) {
              // @ts-expect-error types
              const updatedUser = await FlowClientObject.user.update({
                webapp_user_id: uuidv4(),
              })
              return updatedUser
            }

            if (credentials?.message) {
              if (!projectId) {
                throw new Error('Wallet Connect cloud id is not defined')
              }
              const { message, signature } = credentials
              const address = getAddressFromMessage(message as string)
              const chainId = getChainIdFromMessage(message as string)

              const isValid = await verifySignature({
                address,
                message: message as string,
                signature: signature as string,
                chainId,
                projectId,
              })

              if (
                isValid &&
                !user.web3_wallets.some(
                  (x) => x.wallet_address.toLowerCase() === address.toLowerCase()
                )
              ) {
                // @ts-expect-error types
                const updatedUser = await FlowClientObject.user.update({
                  telegram_user_id: telegram_user_id,
                  wallet_address: address,
                })
                return updatedUser
              }
            }
            return user
          } catch (e) {
            console.error('user was not found. creating a new one with tg id', telegram_user_id, e)
            // create new user
            const snake_case_user_data = transformKeysToSnakeCase(
              tgUserData as unknown as Record<string, unknown>
            ) as TelegramUserDataSnakeCase

            delete snake_case_user_data.id
            // @ts-expect-error types
            const user = await FlowClientObject.user.create({
              ...snake_case_user_data,
              telegram_user_id: parseInt(telegram_user_id),
              webapp_user_id: uuidv4(),
            })
            return user
          }
        } catch (authorizeError) {
          console.error('authorizeError', authorizeError)
          return null
        }
      },
    }),
  ],
  trustHost: true,
  cookies: {
    sessionToken: {
      options: {
        sameSite: 'none',
        secure: true,
      },
    },
    csrfToken: {
      options: {
        secure: true,
        sameSite: 'none',
      },
    },
    callbackUrl: {
      options: {
        secure: true,
        sameSite: 'none',
      },
    },
  },
  session: {
    strategy: 'jwt',
    maxAge: 60 * 15, // 15min
    updateAge: 60 * 10, // 10min
  },
  useSecureCookies: false,
  callbacks: {
    async jwt({ token, user }) {
      if (!user?.webapp_user_id) {
        return token
      }

      token.user = user

      const { access_token, refresh_token } = await FlowClientObject.user.login(user.webapp_user_id)
      token.access_token = access_token
      token.refresh_token = refresh_token
      return token
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (!token) {
        return session
      }
      let access_token = token.access_token as string
      let refresh_token = token.refresh_token as string
      session.user = token.user as User

      // get users on every session call until they are not onboarded yet doesn't have web3wallet
      if (session.user.telegram_user_id && session.user.web3_wallets.length === 0) {
        session.user = await FlowClientObject.user.get(session.user.telegram_user_id.toString())
      }

      if (token.access_token && session.user.webapp_user_id) {
        const decoded = decode(token.access_token as string) as {
          exp: number
          webapp_user_id: string
        }
        const now = new Date().valueOf()
        const exp = decoded?.exp ?? 0
        if (exp * 1000 < now) {
          const newTokens = await FlowClientObject.user.login(session.user.webapp_user_id)

          access_token = newTokens.access_token
          refresh_token = newTokens.refresh_token
        }
      }

      session.access_token = access_token as string
      session.refresh_token = refresh_token as string

      const decoded = decode(session.access_token as string) as {
        exp: number
        webapp_user_id: string
      }
      session.expires = new Date(decoded.exp * 1000) as Date & string
      return session
    },
  },
  debug: process.env.NODE_ENV !== 'production' ? true : false,
})

export default auth
