import Link from 'next/link'
import Image from 'next/image'

import {
  formatDateOnly,
  getLatestSummaries,
  getSummaryByDate,
} from '@/lib/entries'

type Props = {
  params: Promise<{
    date: string
  }>
}

export async function generateStaticParams() {
  return (await getLatestSummaries()).map(entry => ({ date: entry.date }))
}

export const dynamicParams = false

export default async function DayPage({ params }: Props) {
  const { date } = await params
  const entry = await getSummaryByDate(date)

  return (
    <main className="page">
      <div className="wrap narrow">
        <Link className="back-link" href="/">
          ← 日記一覧
        </Link>

        {entry === null ? (
          <div className="empty-state">
            <h1>日記が見つかりません</h1>
            <p>{formatDateOnly(date)} のローカルデータはありません。</p>
          </div>
        ) : (
          <>
            <header className="day-header">
              <p className="eyebrow">VRCHAT DIARY</p>
              <h1 className="day-title">{entry.title}</h1>
              <time className="day-date" dateTime={date}>
                {formatDateOnly(date)}
              </time>
            </header>
            {entry.imageUrl ? (
              <div className="day-image-frame">
                <Image
                  src={entry.imageUrl}
                  alt={`${formatDateOnly(date)}のVRChat記録`}
                  className="day-image"
                  width={960}
                  height={540}
                  sizes="(max-width: 720px) 100vw, 720px"
                />
              </div>
            ) : null}
            <article className="entry-copy">
              <p className="entry-body">{entry.content}</p>
            </article>
          </>
        )}
      </div>
    </main>
  )
}
