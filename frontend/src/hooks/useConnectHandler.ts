'use client'

import { useCallback } from 'react'

import { Chain, getContract, sendTransaction, waitForReceipt } from 'thirdweb'
import { base } from 'thirdweb/chains'
import { addAdmin, getAllAdmins } from 'thirdweb/extensions/erc4337'
import { Wallet } from 'thirdweb/wallets'

import { THIRDWEB_ADMIN_ACCOUNT, THIRDWEB_AUTH_TOKEN_LS_KEY, client } from '@/config/thirdweb'
import { useSession } from '@/hooks/useAuth.compat'

export const useConnectHandler = () => {
  const { data: session, update } = useSession()

  const onConnectHandler = useCallback(
    async (wallet: Wallet) => {
      const account = wallet.getAccount()
      const address = account?.address
      if (!session && address) {
        console.log('logging in!')
        const thirdwebAuthJwt = localStorage.getItem(THIRDWEB_AUTH_TOKEN_LS_KEY)

        const res = await fetch('/api/sign_thirdweb_jwt', {
          method: 'POST',
          body: JSON.stringify({ authJwt: thirdwebAuthJwt }),
        }).then((res) => res.json())
        const signedJWT = res.gurunetwork_thirdweb_jwt
        if (!signedJWT) {
          throw new Error('Failed to sign thirdweb jwt')
        }

        // Get callback URL from current page URL on client side
        const callbackUrl =
          typeof window !== 'undefined'
            ? new URLSearchParams(window.location.search).get('callbackUrl')
            : null

        // Call new login API
        const signInResult = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            jwt: signedJWT,
            wallets: [
              {
                id: wallet.id,
                address: address,
              },
            ],
          }),
          credentials: 'include',
        }).then((res) => res.json())

        console.log('signInResult', signInResult)

        // Refresh session after successful login
        if (signInResult.success) {
          await update()

          // Redirect to callback URL if provided
          if (callbackUrl) {
            window.location.href = callbackUrl
          }
        }

        await Promise.all(
          [base].map(async (chain) => {
            const thirdwebChain: Chain = chain
            const smartAccountAdmins = []
            try {
              const admins = await getAllAdmins({
                contract: getContract({
                  address: address,
                  chain: thirdwebChain,
                  client,
                }),
              })
              console.log(`admins for ${address}`, admins)
              smartAccountAdmins.push(...admins)
            } catch (e) {
              console.error(`Error while getting admins for ${address}`, e)
            } finally {
              if (!smartAccountAdmins.includes(THIRDWEB_ADMIN_ACCOUNT)) {
                console.log('No backend wallet in admins. Adding it as an admin')
                const transaction = addAdmin({
                  contract: getContract({
                    address: address,
                    chain: thirdwebChain,
                    client,
                  }),
                  account: account,
                  adminAddress: THIRDWEB_ADMIN_ACCOUNT,
                })
                try {
                  const receiptOptions = await sendTransaction({ transaction, account })
                  console.log('Sent txn', JSON.stringify(transaction), account)
                  console.log('txn hash', receiptOptions.transactionHash)
                  const receipt = await waitForReceipt(receiptOptions)
                  console.log('receipt', receipt)
                } catch (e) {
                  console.error('error during add Admin txn', e)
                }
              }
            }
          })
        )
      }
    },
    [session?.user?.id, update]
  )

  return { onConnectHandler }
}
