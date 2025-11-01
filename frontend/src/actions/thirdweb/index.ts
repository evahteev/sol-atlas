'use server'

import { cookies } from 'next/headers'

import { THIRDWEB_JWT_COOKIE_NAME } from '@/config/settings'

export async function logout() {
  const cookiesStore = await cookies()
  cookiesStore.delete(THIRDWEB_JWT_COOKIE_NAME)
}
