import { cookies } from 'next/headers'

import jwt from 'jsonwebtoken'

import { THIRDWEB_JWT_COOKIE_NAME } from '@/config/settings'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { authJwt } = body
    if (!authJwt) {
      throw new Error('No authJwt provided')
    }
    const secret = process.env.AUTHJWT_SECRET_KEY
    if (!secret) {
      throw new Error('No secret provided to sign jwt')
    }
    const cookiesStore = await cookies()
    const payloadJWT = jwt.decode(authJwt) as jwt.JwtPayload
    const userWalletId = payloadJWT.storedToken.authDetails.userWalletId
    if (!userWalletId) {
      throw new Error('userWalletId was not found in thirdweb authToken')
    }
    try {
      if (payloadJWT) {
        payloadJWT.sub = userWalletId
        payloadJWT.type = 'access'
        const token = jwt.sign(payloadJWT, secret, {
          algorithm: 'HS256',
        })

        cookiesStore.set(THIRDWEB_JWT_COOKIE_NAME, token, {
          httpOnly: true,
          secure: true,
        })
        return Response.json({ success: true, gurunetwork_thirdweb_jwt: token })
      }
    } catch (error) {
      throw new Error(`Can't sign payloadJWT with secret: ${error}`)
    }
  } catch (e) {
    return new Response(`Can't create cookie: ${JSON.stringify(e)}`, { status: 500 })
  }
}
