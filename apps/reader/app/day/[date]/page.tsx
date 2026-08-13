import Link from 'next/link'

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
  return (await getLatestSummaries(60)).map(entry => ({ date: entry.date }))
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
            <p>{formatDateOnly(date)} の公開日記はありません。</p>
          </div>
        ) : (
          <>
            <header className="day-header">
              <p className="eyebrow">DIARY / 日記</p>
              <h1 className="day-title">{entry.title}</h1>
              <time className="day-date" dateTime={date}>
                {formatDateOnly(date)}
              </time>
              <p className="artifact-note">
                その日の出来事を読み返すためにまとめた記録です。会話や写真などの元記録そのものではありません。
              </p>
            </header>
            <article className="entry-copy">
              <p className="entry-body">{entry.content}</p>
            </article>
          </>
        )}
      </div>
    </main>
  )
}
