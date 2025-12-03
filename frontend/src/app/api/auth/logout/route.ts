import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

import { THIRDWEB_JWT_COOKIE_NAME } from '@/config/settings'
import { deleteSession } from '@/lib/session'

export async function POST() {
  try {
    // Delete session cookie
    await deleteSession()

    // Also delete Thirdweb JWT cookie
    const cookieStore = await cookies()
    cookieStore.delete(THIRDWEB_JWT_COOKIE_NAME)

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Logout error:', error)
    return NextResponse.json(
      {
        error: 'Logout failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}
