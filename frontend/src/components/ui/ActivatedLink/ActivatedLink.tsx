'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { AnchorHTMLAttributes } from 'react'

import clsx from 'clsx'
import { UrlObject, format } from 'url'

type ActivatedLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  href: string | UrlObject
  activeClassName: string
  exact?: boolean
}

function isPathActive(currentPath: string, targetPath: string, exact: boolean = false): boolean {
  if (exact) {
    return targetPath === currentPath
  }

  return currentPath.startsWith(targetPath)
}

export function ActivatedLink({
  children,
  className,
  href,
  activeClassName,
  exact = false,
}: ActivatedLinkProps) {
  const pathname = usePathname()
  const acticatedLinkClassName = clsx(className, {
    [activeClassName]: isPathActive(pathname, format(href), exact),
  })
  return (
    <Link href={href} className={acticatedLinkClassName}>
      {children}
    </Link>
  )
}
