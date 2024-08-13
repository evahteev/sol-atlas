import { PrismaAdapter } from '@auth/prisma-adapter'
import { PrismaClient } from '@prisma/client'
import { getAddressFromMessage, getChainIdFromMessage, verifySignature } from '@web3modal/siwe'
import NextAuth from 'next-auth'
import credentialsProvider from 'next-auth/providers/credentials'
import { v4 as uuidv4 } from 'uuid'

import { WALLET_CONNECT_PROJECT_ID } from '@/config/settings'
import FlowClient from '@/services/flow/client'
import { removeJWT } from '@/services/siwe'

const nextAuthSecret = process.env.AUTH_SECRET
if (!nextAuthSecret) {
  throw new Error('AUTH_SECRET is not set')
}

const projectId = WALLET_CONNECT_PROJECT_ID
if (!projectId) {
  throw new Error('NEXT_PUBLIC_PROJECT_ID is not set')
}

export const prisma = new PrismaClient()

const providers = [
  credentialsProvider({
    name: 'Ethereum',
    credentials: {
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
      name: {
        label: 'Anonymous',
        type: 'text',
        placeholder: '0x0',
      },
    },
    async authorize(credentials) {
      try {
        if (!credentials?.message) {
          if (!credentials?.name) {
            throw new Error('SiweMessage or Anonymous name are undefined')
          }
          const { id, name } = credentials as { id?: string; name: string }
          let user = id
            ? await prisma.user.findUnique({
                where: { id },
              })
            : null

          if (!user || (id === undefined && name === 'Anonymous')) {
            const anonymousId = uuidv4()
            user = await prisma.user.create({
              data: { name: `${anonymousId}`, email: `${anonymousId}@anonymous.com` },
            })
            const flowClient = new FlowClient()
            await flowClient.createUser({ webapp_user_id: user.id })
          }
          return user
        }

        const { message, signature } = credentials as { message: string; signature: string }
        const address = getAddressFromMessage(message)
        const chainId = getChainIdFromMessage(message)

        const isValid = await verifySignature({ address, message, signature, chainId, projectId })

        if (isValid) {
          let user = await prisma.user.findUnique({
            where: { email: `${address}@gurunetwork.ai` },
          })

          if (!user) {
            user = await prisma.user.create({
              data: { name: address, email: `${address}@gurunetwork.ai` },
            })
          }

          return user
        } else {
          console.error('Signature verification failed')
          return null
        }
      } catch (e) {
        console.error('Error in authorize function:', e)
        return null
      }
    },
  }),
]

export const { auth, handlers, signIn, signOut } = NextAuth({
  secret: nextAuthSecret,
  adapter: PrismaAdapter(prisma),
  trustHost: true,
  providers,
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.id = user.id
      }
      return token
    },
    session({ session, token }) {
      session.user.id = token.id as string
      return session
    },
  },
  events: {
    signOut() {
      removeJWT()
    },
  },
  debug: process.env.NODE_ENV !== 'production' ? true : false,
})
