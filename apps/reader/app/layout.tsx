import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'VRChat Auto Diary',
  description: 'VRChatで過ごした時間を読み返す日記',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}
