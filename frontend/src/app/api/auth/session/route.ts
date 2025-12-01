import { NextResponse } from 'next/server'

import { getSessionWithUser } from '@/lib/dal'

export async function GET() {
  try {
    const session = await getSessionWithUser()

    if (!session) {
      return NextResponse.json({ session: null }, { status: 200 })
    }

    return NextResponse.json({ session })
  } catch (error) {
    console.error('Session fetch error:', error)
    return NextResponse.json(
      {
        error: 'Failed to fetch session',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}
