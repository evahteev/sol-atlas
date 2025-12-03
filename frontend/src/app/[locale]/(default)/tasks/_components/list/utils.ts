export const getFilter = (tab?: string, isNFTHolder?: boolean) => {
  if (tab === 'onboarding') {
    return '^onboarding.*'
  }

  if (tab === 'mainnet') {
    return isNFTHolder ? 'quest_daonft' : 'quest_nodaonft'
  }

  if (tab === 'minima') {
    return 'quest_minima'
  }

  return '^quest(?!_daonft$|_nodaonft$).*'
}
