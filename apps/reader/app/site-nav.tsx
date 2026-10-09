'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import {
  PRIMARY_NAVIGATION,
  navigationItemIsActive,
} from '@/lib/navigation'

import styles from './site-nav.module.css'

export default function SiteNav() {
  const pathname = usePathname()

  return (
    <nav className={styles.shell} aria-label="KafLogの記憶を読む">
      <div className={styles.inner}>
        <Link href="/" className={styles.brand} aria-label="KafLog ホーム">
          KafLog
        </Link>

        <ul className={styles.items}>
          {PRIMARY_NAVIGATION.map(item => {
            const active = navigationItemIsActive(item, pathname)

            return (
              <li key={item.key}>
                {item.href ? (
                  <Link
                    href={item.href}
                    className={styles.link}
                    aria-current={active ? 'page' : undefined}
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span
                    className={styles.disabled}
                    aria-disabled="true"
                    title="この読み方は準備中です"
                  >
                    {item.label}
                    <span className={styles.soon}>準備中</span>
                  </span>
                )}
              </li>
            )
          })}
        </ul>
      </div>
    </nav>
  )
}
