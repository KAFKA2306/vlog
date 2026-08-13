import Link from 'next/link'
import Image from 'next/image'

import { formatDateOnly, getLatestSummaries } from '@/lib/entries'

export default async function Page() {
  const entries = await getLatestSummaries()

  return (
    <main className="page">
      <div className="wrap">
        <header className="site-header">
          <p className="eyebrow">PUBLISHED DAYS</p>
          <h1 className="site-title">VRChat Auto Diary</h1>
          <p className="site-intro">
            VRChatで過ごした時間を、日付ごとの記録として読み返せます。
          </p>
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
                    {entry.imageUrl ? (
                      <div className="entry-image-frame">
                        <Image
                          src={entry.imageUrl}
                          alt={`${formatDateOnly(entry.date)}のVRChat記録`}
                          className="entry-image"
                          width={640}
                          height={360}
                          sizes="(max-width: 720px) 100vw, 440px"
                        />
                      </div>
                    ) : null}
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
