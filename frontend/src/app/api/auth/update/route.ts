import { NextRequest, NextResponse } from 'next/server'

import { updateSessionData } from '@/lib/dal'
import { getSession } from '@/lib/session'

/**
 * PATCH /api/auth/update
 *
 * Update session cookie with new/modified data
 * This endpoint allows partial updates to the session without full re-authentication
 *
 * Request body should contain partial session data to merge with existing session
 */
export async function PATCH(request: NextRequest) {
  try {
    // Verify current session exists
    const currentSession = await getSession()
    if (!currentSession) {
      return NextResponse.json({ error: 'No active session found' }, { status: 401 })
    }

    // Parse update data from request
    const updates = await request.json()

    // Update session cookie with merged data
    const updatedSession = await updateSessionData(updates)

    if (!updatedSession) {
      return NextResponse.json({ error: 'Failed to update session' }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      session: updatedSession,
    })
  } catch (error) {
    console.error('Session update error:', error)
    return NextResponse.json(
      {
        error: 'Failed to update session',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}
