import Link from 'next/link'
import Image from 'next/image'

import { formatDateOnly, getPublishedEntries } from '@/lib/entries'

export default async function Page() {
  const entries = await getPublishedEntries()

  return (
    <main className="page home-page">
      <div className="wrap home-wrap">
        <header className="site-header">
          <div className="topline">
            <span className="wordmark">VLOG / READER</span>
            <span className="status-chip"><span aria-hidden="true" /> PUBLIC PROJECTION</span>
          </div>
          <div className="hero-grid">
            <div>
              <p className="eyebrow">MEMORY FIELD NOTES</p>
              <h1 className="site-title">The days that stayed with you.</h1>
              <p className="site-intro">
                VRChatで過ごした時間を、日付ごとの記録として読み返せます。
              </p>
            </div>
            <aside className="archive-card" aria-label="公開記録の件数">
              <span className="archive-label">ARCHIVE / 2026</span>
              <strong>{String(entries.length).padStart(2, '0')}</strong>
              <span className="archive-caption">published fragments</span>
            </aside>
          </div>
        </header>

        {entries.length === 0 ? (
          <div className="empty-state">
            <p>まだ日記がありません。</p>
          </div>
        ) : (
          <section className="entries-section" aria-labelledby="latest-heading">
            <div className="section-heading">
              <div>
                <p className="eyebrow">RECENTLY PUBLISHED</p>
                <h2 id="latest-heading">Latest traces</h2>
              </div>
              <span className="section-count">{String(entries.length).padStart(2, '0')} DAYS</span>
            </div>
            <ol className="entries">
            {entries.map((entry, index) => {
              const preview = entry.content.replace(/\s+/g, ' ').slice(0, 140)
              const label = entry.source === 'novel' ? '小説' : '日記'

              return (
                <li key={entry.id} className={index === 0 ? 'entry-item entry-item-featured' : 'entry-item'}>
                  <Link
                    href={'/entry/' + entry.id}
                    className={index === 0 ? 'entry-link entry-featured' : 'entry-link'}
                    aria-label={formatDateOnly(entry.date) + 'の' + label + 'を読む'}
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
                    <div className="entry-meta">
                      <span className="entry-index">{String(index + 1).padStart(2, '0')}</span>
                      <time className="entry-date" dateTime={entry.date}>
                        {formatDateOnly(entry.date)}
                      </time>
                      <span className={'entry-type ' + entry.source}>
                        {entry.source === 'novel' ? 'NOVEL' : 'DIARY'}
                      </span>
                    </div>
                    <strong className="entry-title">{entry.title}</strong>
                    {preview ? (
                      <span className="entry-preview">{preview}</span>
                    ) : null}
                    <span className="entry-action" aria-hidden="true">
                      {label}を読む →
                    </span>
                  </Link>
                </li>
              )
            })}
            </ol>
          </section>
        )}
      </div>
    </main>
  )
}
