import Link from 'next/link'

import { formatDateOnly, getLatestSummaries } from '@/lib/entries'
import { HOME_COPY } from '@/lib/site-copy'

export default async function Page() {
  const entries = await getLatestSummaries(60)

  return (
    <main className="page">
      <div className="wrap">
        <header className="site-header">
          <p className="eyebrow">{HOME_COPY.eyebrow}</p>
          <h1 className="site-title">{HOME_COPY.title}</h1>
          <p className="site-intro">{HOME_COPY.intro}</p>
        </header>

        {entries.length === 0 ? (
          <div className="empty-state">
            <p>まだ日記がありません。</p>
          </div>
        ) : (
          <ol className="entries">
            {entries.map(entry => {
              const preview = entry.content.replace(/\s+/g, ' ').slice(0, 140)

              return (
                <li key={entry.id}>
                  <Link
                    href={'/day/' + entry.date}
                    className="entry-link"
                    aria-label={formatDateOnly(entry.date) + 'の日記を読む'}
                  >
                    <time className="entry-date" dateTime={entry.date}>
                      {formatDateOnly(entry.date)}
                    </time>
                    <strong className="entry-title">{entry.title}</strong>
                    {preview ? (
                      <span className="entry-preview">{preview}</span>
                    ) : null}
                    <span className="entry-action" aria-hidden="true">
                      日記を読む →
                    </span>
                  </Link>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </main>
  )
}
