import Link from 'next/link'

import { ARTIFACT_SEMANTICS } from '@/lib/artifact-semantics'
import { formatDateOnly } from '@/lib/entries'
import { getPublicNovels, novelPermalink } from '@/lib/novels'

import styles from './page.module.css'

export default async function NovelsPage() {
  const novels = await getPublicNovels(60)

  return (
    <main className="page">
      <div className="wrap">
        <header className="site-header">
          <p className="eyebrow">{ARTIFACT_SEMANTICS.novel.label}</p>
          <h1 className="site-title">記憶から生まれた物語</h1>
          <p className="site-intro">
            {ARTIFACT_SEMANTICS.novel.archiveDescription}
          </p>
        </header>

        {novels.length === 0 ? (
          <div className="empty-state">
            <h2>公開された物語はまだありません。</h2>
            <p>非公開のNovelをReaderへ補完表示することはありません。</p>
          </div>
        ) : (
          <ol className="entries">
            {novels.map(novel => {
              const preview = novel.content.replace(/\s+/g, ' ').slice(0, 140)

              return (
                <li key={novel.id}>
                  <Link
                    href={novelPermalink(novel.id)}
                    className={`${styles.novelCard} entry-link`}
                    aria-label={`${formatDateOnly(novel.date)}の物語「${novel.title}」を読む`}
                  >
                    <span className={styles.kind}>Novel / 物語</span>
                    <time className="entry-date" dateTime={novel.date}>
                      {formatDateOnly(novel.date)}
                    </time>
                    <strong className="entry-title">{novel.title}</strong>
                    <span className="entry-preview">{preview}</span>
                    <span className="entry-action" aria-hidden="true">
                      物語を読む →
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
