import { redirect } from 'next/navigation'

export default async function SignInPage() {
  return (
    <form
      action={async (formData) => {
        'use server'
        try {
          const jwt = formData.get('jwt') as string
          const wallets = formData.get('wallets') as string

          const response = await fetch(`${process.env.NEXT_PUBLIC_APP_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              jwt,
              wallets: wallets ? JSON.parse(wallets) : [],
            }),
          })

          const result = await response.json()

          if (!result.success) {
            return redirect(`/login?error=${result.error || 'Login failed'}`)
          }

          return redirect('/')
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error'
          return redirect(`/login?error=${errorMessage}`)
        }
      }}>
      <label htmlFor="jwt">
        Thirdweb JWT
        <input name="jwt" id="jwt" />
      </label>
      <label htmlFor="wallets">
        Thirdweb Wallets (JSON array)
        <input name="wallets" id="wallets" />
      </label>
      <input type="submit" value="Sign In" />
    </form>
  )
}
