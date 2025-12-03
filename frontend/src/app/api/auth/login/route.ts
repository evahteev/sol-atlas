import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

import { decodeJwt, jwtVerify } from 'jose'
import { WalletId } from 'thirdweb/wallets'
import { validate } from 'uuid'

import {
  REF_USER_ID_COOKIE_NAME,
  THIRDWEB_ECOSYSTEM_ID,
  THIRDWEB_JWT_COOKIE_NAME,
} from '@/config/settings'
import { createSession } from '@/lib/session'
import { FlowClientObject } from '@/services/flow'

const userHasWallet = (
  user: { web3_wallets: { wallet_address: string }[] },
  wallet_address: string
): boolean => {
  return user?.web3_wallets?.some(
    (x) => x.wallet_address.toLowerCase() === wallet_address.toLowerCase()
  )
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { jwt: thirdwebJWT, wallets } = body

    if (!thirdwebJWT || !wallets) {
      return NextResponse.json({ error: 'Missing jwt or wallets in request body' }, { status: 400 })
    }

    if (!process.env.AUTHJWT_SECRET_KEY) {
      throw new Error('AUTHJWT_SECRET_KEY is not defined')
    }

    // Verify Thirdweb JWT
    const secret = new TextEncoder().encode(process.env.AUTHJWT_SECRET_KEY)
    const { payload: decodedJWT } = await jwtVerify<{
      storedToken: { authDetails: { userWalletId: string }; authProvider: string; jwtToken: string }
    }>(thirdwebJWT, secret, {
      algorithms: ['HS256'],
    })

    const webAppUserId = decodedJWT.storedToken.authDetails.userWalletId
    const authProvider = decodedJWT.storedToken.authProvider
    const decodedProviderJWT = decodeJwt(decodedJWT.storedToken.jwtToken)

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

      const parsedWallets = Array.isArray(wallets) ? wallets : JSON.parse(wallets)

      await Promise.all(
        parsedWallets.map(async (wallet: { id: WalletId; address?: string }) => {
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

    let user

    try {
      user = await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
      await upsertWallets(user)
      user = await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
    } catch (authError) {
      if (!(authError instanceof Error) || !authError.message.includes('User not found')) {
        throw new Error(`Error getting user data from thirdweb: ${JSON.stringify(authError)}`)
      }

      try {
        if (authProvider === 'Telegram' && decodedProviderJWT.sub) {
          const telegram_user_id = decodedProviderJWT.sub

          user = await FlowClientObject.user.get({ telegram_user_id }).catch(async () => {
            // @ts-expect-error - Flow API types are incomplete
            const newUser = await FlowClientObject.user.create({
              telegram_user_id: parseInt(telegram_user_id),
              username: (decodedProviderJWT.username as string) || null,
              first_name: (decodedProviderJWT.firstName as string) || null,
              last_name: (decodedProviderJWT.lastName as string) || null,
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
          user = await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
        } else {
          // Fallback for non-Telegram users
          // @ts-expect-error types
          user = await FlowClientObject.user.create({
            webapp_user_id: webAppUserId,
            is_block: true,
            ref_user_id: validate(refUserId) ? refUserId : undefined,
          })
          await upsertWallets(user)
          user = await FlowClientObject.user.get({ webapp_user_id: webAppUserId })
        }
      } catch (e) {
        console.error("Can't create user with thirdweb", e)
        throw e
      }
    }

    // Create session with minimal data
    await createSession(user.id, {
      webapp_user_id: user.webapp_user_id!,
      is_admin: user.is_admin,
      is_block: user.is_block,
      telegram_user_id: user.telegram_user_id,
      camunda_user_id: user.camunda_user_id,
    })

    // Store Thirdweb JWT separately for API calls
    cookieStore.set(THIRDWEB_JWT_COOKIE_NAME, thirdwebJWT, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60 * 24, // 24 hours
      sameSite: 'lax',
      path: '/',
    })

    return NextResponse.json({
      success: true,
      user: {
        id: user.id,
        webapp_user_id: user.webapp_user_id,
        is_admin: user.is_admin,
        is_block: user.is_block,
        telegram_user_id: user.telegram_user_id,
        camunda_user_id: user.camunda_user_id,
      },
    })
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      {
        error: 'Authentication failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 401 }
    )
  }
}
