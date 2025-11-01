export async function GET() {
  const llms = `# https://dex.guru llms.txt

- [Stake and Earn $GURU](https://dex.guru): Maximize earnings through staking and rewards with $GURU.
- [Maximize Your Staking Earnings](https://dex.guru/staking/can-wait): Stake $GURU to maximize your earnings and rewards.
- [Staking $GURU Rewards](https://dex.guru/staking/wait-some): Maximize earnings by staking $GURU for rewards.
- [Maximize Staking Earnings](https://dex.guru/staking/rapid): Stake $GURU to maximize your earnings with AIGURU.
- [Maximize Staking Earnings](https://dex.guru/staking/loot): Stake $GURU to maximize your earnings effectively.
- [Staking Support Page](https://dex.guru/staking/support): Get assistance and maximize earnings through GURU staking.
- [Staking and Rewards](https://dex.guru/staking): Maximize earnings by staking $GURU and earning AIGURU.
- [Staking and Referral Program](https://dex.guru/staking/referral): Maximize earnings through staking and referral opportunities.
- [Buy $GURU Token](https://dex.guru/buy): Purchase $GURU and earn rewards through staking options.`

  const headers = new Headers({ 'content-type': 'text/plain' })

  return new Response(llms, { headers })
}
