import { FC } from 'react'

import clsx from 'clsx'

import { getTokenCoinGeckoData } from '@/actions/tokens/coingecko'
import { ButtonProps } from '@/components/ui/Button'
import ButtonGroup from '@/components/ui/ButtonGroup'
import IconLink from '@/images/icons/link.svg'
import IconFacebook from '@/images/socials/facebook.svg'
import IconTelegram from '@/images/socials/telegram.svg'
import IconX from '@/images/socials/x.svg'
import { TokenV3Model } from '@/models/token'
import { getAsArray } from '@/utils'

import styles from './links.module.scss'

export const TokenOverviewLinksCommunity: FC<{ className?: string; token: TokenV3Model }> = async ({
  token,
  className,
}) => {
  const data = await getTokenCoinGeckoData(token.address, token.network)

  if (!data?.links) {
    return null
  }

  const linksFiltered = Object.entries(data.links)
    .map(([key, value]) => [key, getAsArray(value)?.filter((item) => !!item)])
    .filter(([key, value]) => key !== 'repos_url' && !!value?.length)

  if (!linksFiltered.length) {
    return null
  }

  const linksFilteredObj = Object.fromEntries(linksFiltered)

  const buttons: ButtonProps[] = []
  if (linksFilteredObj.homepage?.[0]) {
    buttons.push({
      className: styles.link,
      icon: <IconLink className={styles.icon} />,
      href: linksFilteredObj.homepage?.[0],
      target: '_blank',
      rel: 'noopener noreferrer',
    })
  }
  if (linksFilteredObj.telegram_channel_identifier?.[0]) {
    buttons.push({
      className: styles.link,
      icon: <IconTelegram className={styles.icon} />,
      href: `https://t.me/${linksFilteredObj.telegram_channel_identifier?.[0]}`,
      target: '_blank',
      rel: 'noopener noreferrer',
    })
  }
  if (linksFilteredObj.twitter_screen_name?.[0]) {
    buttons.push({
      className: styles.link,
      icon: <IconX className={styles.icon} />,
      href: `https://x.com/${linksFilteredObj.twitter_screen_name?.[0]}`,
      target: '_blank',
      rel: 'noopener noreferrer',
    })
  }
  if (linksFilteredObj.facebook_username?.[0]) {
    buttons.push({
      className: styles.link,
      icon: <IconFacebook className={styles.icon} />,
      href: `https://facebook.com/${linksFilteredObj.facebook_username?.[0]}`,
      target: '_blank',
      rel: 'noopener noreferrer',
    })
  }

  return (
    <ButtonGroup
      isOutline
      size="sm"
      buttons={buttons}
      className={clsx(styles.community, className)}
    />
  )
}
