import { FC } from 'react'

import clsx from 'clsx'

import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { TokenTagModel } from '@/models/token'

import { TokensTagsCloudTagIcon } from './icon'

import styles from './cloud.module.scss'

type TokensExplorerTagsCloudProps = {
  className?: string
  tags?: TokenTagModel[]
}

export const TokensTagsCloud: FC<TokensExplorerTagsCloudProps> = ({ className, tags }) => {
  return (
    <>
      <div className={clsx(styles.container, className)}>
        <Show if={tags?.length}>
          <ul className={styles.list}>
            {tags?.map((tag) => {
              return (
                <li className={styles.item} key={tag.id}>
                  <Button
                    icon={
                      tag.logo_uri ? (
                        <TokensTagsCloudTagIcon tag={tag} className={styles.icon} />
                      ) : undefined
                    }
                    caption={tag.tag_name}
                    variant="custom"
                    size="sm"
                    className={styles.tag}
                    href={`/tokens/tag/${tag.id}`}
                  />
                </li>
              )
            })}
          </ul>
        </Show>
      </div>
    </>
  )
}
