import auth from '@/auth'
import ButtonConnect from '@/components/composed/ButtonConnect'
import { ActionPanel } from '@/components/page'
import { Show } from '@/components/ui'

import { ProfileWalletsAddress } from './_components/address/address'
import { ProfileWalletsBalance } from './_components/balance/balance'
import { ProfileWalletsSection } from './_components/section/section'

import styles from './_assets/page.module.scss'

export default async function ProfileWallets() {
  const session = await auth()

  const externalWallets = session?.user.web3_wallets.filter((x) => x.network_type === 'eth')

  return (
    <>
      <div className={styles.body}>
        <ProfileWalletsSection title="Internal Wallet">
          <ProfileWalletsAddress
            address={session?.user.web3_wallets?.[0]?.wallet_address || ''}
            action={<ProfileWalletsBalance />}
          />
        </ProfileWalletsSection>

        <Show if={externalWallets?.length}>
          <ProfileWalletsSection title="External Wallets">
            <ul className={styles.list}>
              {externalWallets?.map((wallet) => (
                <li className={styles.item} key={wallet.id}>
                  <ProfileWalletsAddress
                    address={wallet.wallet_address}
                    // action={<ProfileWalletsAddressRemove address={wallet.wallet_address} />}
                  />
                </li>
              ))}
            </ul>
          </ProfileWalletsSection>
        </Show>
      </div>

      <ActionPanel className={styles.panel}>
        <ButtonConnect />
      </ActionPanel>
    </>
  )
}
