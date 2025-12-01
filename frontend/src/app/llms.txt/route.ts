export async function GET() {
  const llms = `# https://gurunetwork.ai llms.txt

- [Stake and Earn $GURU](https://gurunetwork.ai): Maximize earnings through staking and rewards with $GURU.
- [Maximize Your Staking Earnings](https://gurunetwork.ai/staking/can-wait): Stake $GURU to maximize your earnings and rewards.
- [Staking $GURU Rewards](https://gurunetwork.ai/staking/wait-some): Maximize earnings by staking $GURU for rewards.
- [Maximize Staking Earnings](https://gurunetwork.ai/staking/rapid): Stake $GURU to maximize your earnings with AIGURU.
- [Maximize Staking Earnings](https://gurunetwork.ai/staking/loot): Stake $GURU to maximize your earnings effectively.
- [Staking Support Page](https://gurunetwork.ai/staking/support): Get assistance and maximize earnings through GURU staking.
- [Staking and Rewards](https://gurunetwork.ai/staking): Maximize earnings by staking $GURU and earning AIGURU.
- [Staking and Referral Program](https://gurunetwork.ai/staking/referral): Maximize earnings through staking and referral opportunities.
- [Buy $GURU Token](https://gurunetwork.ai/buy): Purchase $GURU and earn rewards through staking options.`

  const headers = new Headers({ 'content-type': 'text/plain' })

  return new Response(llms, { headers })
}
