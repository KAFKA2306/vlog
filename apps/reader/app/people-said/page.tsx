import Link from 'next/link'

import { formatDateOnly } from '@/lib/entries'
import {
  evidenceLevelLabel,
  getPeopleSaidEntries,
  publicSpeakerLabel,
} from '@/lib/people-said'

export default async function PeopleSaidPage() {
  const entries = await getPeopleSaidEntries()

  return (
    <main className="page">
      <div className="wrap narrow">
        <Link href="/" className="back-link">
          ← KafLogへ戻る
        </Link>

        <header className="people-said-header">
          <p className="eyebrow">PEOPLE SAID</p>
          <h1 className="day-title">人から言われたこと</h1>
          <p className="site-intro">
            公開を選んだ言葉だけを、逐語引用・要約・推測を混同しない形で残しています。
          </p>
        </header>

        {entries.length === 0 ? (
          <div className="empty-state people-said-empty">
            <h2>まだ公開された言葉はありません。</h2>
            <p>非公開の記録や元の会話ログは、このReaderには表示されません。</p>
          </div>
        ) : (
          <ol className="people-said-list">
            {entries.map(entry => {
              const date = entry.occurredAt.slice(0, 10)
              const label = evidenceLevelLabel(entry.evidenceLevel)

              return (
                <li key={`${entry.id}:${entry.publicationDecisionId}`}>
                  <article
                    className={`people-said-card people-said-${entry.evidenceLevel}`}
                  >
                    <div className="people-said-meta">
                      <time dateTime={entry.occurredAt}>{formatDateOnly(date)}</time>
                      <span className="evidence-badge">{label}</span>
                    </div>

                    <p className="people-said-context">
                      {entry.context ?? '文脈は公開していません'}
                    </p>

                    {entry.evidenceLevel === 'direct_quote' ? (
                      <blockquote className="people-said-quote">
                        <p>「{entry.text}」</p>
                      </blockquote>
                    ) : (
                      <p className="people-said-text">{entry.text}</p>
                    )}

                    <p className="people-said-speaker">
                      {publicSpeakerLabel(entry.speakerLabel)}
                    </p>

                    {entry.reaction ? (
                      <aside className="people-said-reaction">
                        <span>その時の自分</span>
                        <p>{entry.reaction}</p>
                      </aside>
                    ) : null}
                  </article>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </main>
  )
}
