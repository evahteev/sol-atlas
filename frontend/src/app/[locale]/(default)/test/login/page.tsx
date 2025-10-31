import { redirect } from 'next/navigation'

import { AuthError } from 'next-auth'

import { signIn } from '@/auth'

export default async function SignInPage() {
  return (
    <form
      action={async (formData) => {
        'use server'
        try {
          await signIn('credentials', formData)
        } catch (error) {
          if (error instanceof AuthError) {
            return redirect(`/login?error=${error.message}`)
          }
          throw error
        }
      }}>
      <label htmlFor="jwt">
        Thirdweb JWT
        <input name="jwt" id="jwt" />
      </label>
      <label htmlFor="wallets">
        Thirdweb Wallets
        <input name="wallets" id="wallets" />
      </label>
      <input type="submit" value="Sign In" />
    </form>
  )
}
