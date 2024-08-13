'use client'

import type { User } from '@prisma/client'
import { createSIWEConfig, formatMessage } from '@web3modal/siwe'
import type { SIWECreateMessageArgs, SIWEVerifyMessageArgs } from '@web3modal/siwe'
import { getCsrfToken, getSession, signIn, signOut } from 'next-auth/react'

import { LocalStorageKeyEnum } from '@/config/settings'
import { supportedChains } from '@/config/wagmi'

import FlowClient from '../flow/client'

async function getJWT(id: string) {
  const flowClient = new FlowClient()

  const { access_token, refresh_token } = await flowClient.loginUser(id)
  if (typeof window !== 'undefined') {
    localStorage.setItem(LocalStorageKeyEnum.access_token, access_token)
    localStorage.setItem(LocalStorageKeyEnum.refresh_token, refresh_token)
  }
}
export function removeJWT() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(LocalStorageKeyEnum.access_token)
    localStorage.removeItem(LocalStorageKeyEnum.refresh_token)
  }
}

/* Create a SIWE configuration object */
export const siweConfig = createSIWEConfig({
  getMessageParams: async () => ({
    domain: typeof window !== 'undefined' ? window.location.host : '',
    uri: typeof window !== 'undefined' ? window.location.origin : '',
    chains: supportedChains.map((chain) => chain.id),
    statement: 'Please sign with your account',
  }),
  createMessage: ({ address, ...args }: SIWECreateMessageArgs) => {
    return formatMessage({ ...args, iat: new Date().toISOString() }, address)
  },
  getNonce: async () => {
    const nonce = await getCsrfToken()
    if (!nonce) {
      throw new Error('Failed to get nonce!')
    }

    return nonce
  },
  getSession: async () => {
    const session = await getSession()
    if (!session) {
      throw new Error('Failed to get session!')
    }

    const { user } = session
    if (!user) {
      throw new Error('Failed to get user from session!')
    }

    const address = user?.name
    if (!address) {
      throw new Error('Failed to get user address from session!')
    }
    const access_token = localStorage.getItem(LocalStorageKeyEnum.access_token) ?? undefined
    const refresh_token = localStorage.getItem(LocalStorageKeyEnum.refresh_token) ?? undefined

    return { address, chainId: 1, access_token, refresh_token }
  },
  verifyMessage: async ({ message, signature }: SIWEVerifyMessageArgs) => {
    try {
      const success = await signIn('credentials', {
        message,
        redirect: false,
        signature,
        callbackUrl: '/',
      })

      return Boolean(success?.ok)
    } catch (error) {
      return false
    }
  },
  signOut: async () => {
    try {
      removeJWT()
      await signOut({
        redirect: false,
      })

      return true
    } catch (error) {
      return false
    }
  },
  onSignOut: async () => {
    try {
      removeJWT()
      await signOut({
        redirect: false,
      })

      return true
    } catch (error) {
      return false
    }
  },
  onSignIn: async () => {
    const session = await getSession()
    if (session === undefined) {
      console.error('there is no session onSignIn')
      return
    }
    const { user } = session as unknown as { user: User }
    const { id } = user
    try {
      await getJWT(id)
    } catch (e) {
      console.error(e)
      const flowClient = new FlowClient()
      await flowClient.createUser({ webapp_user_id: id })
      getJWT(id)
    }
  },

  signOutOnDisconnect: true,
  signOutOnAccountChange: true,
  signOutOnNetworkChange: false,
})
