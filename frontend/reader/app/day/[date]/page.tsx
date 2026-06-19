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
        <h1 className="site-title">{formatDateOnly(date)}</h1>
        <p className="day-url">/day/{date}</p>
        <Link className="back-link" href="/">
          Home
        </Link>

        {entry === null ? (
          <div className="empty-state">
            <p>No local content found for this day.</p>
            <Link className="back-link" href="/">
              Home
            </Link>
          </div>
        ) : (
          <article className="entry-copy">
            <h2>{entry.title}</h2>
            <p className="entry-preview">{entry.content}</p>
          </article>
        )}
      </div>
    </main>
  )
}
