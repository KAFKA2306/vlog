import './globals.css'
import type { Metadata } from 'next'

import { SITE_METADATA } from '@/lib/site-copy'

import SiteNav from './site-nav'

export const metadata: Metadata = {
  title: SITE_METADATA.title,
  description: SITE_METADATA.description,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <SiteNav />
        {children}
      </body>
    </html>
  )
}
