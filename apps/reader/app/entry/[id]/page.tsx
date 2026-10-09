import Image from 'next/image'
import Link from 'next/link'

import { formatDateOnly, getEntryById, getPublishedEntries } from '@/lib/entries'

type Props = {
  params: Promise<{
    id: string
  }>
}

export async function generateStaticParams() {
  return (await getPublishedEntries()).map(entry => ({ id: entry.id }))
}

export const dynamicParams = false

export default async function EntryPage({ params }: Props) {
  const { id } = await params
  const entry = await getEntryById(id)

  return (
    <main className="page">
      <div className="wrap narrow">
        <Link className="back-link" href="/">
          ← 一覧に戻る
        </Link>

        {entry === null ? (
          <div className="empty-state">
            <h1>記事が見つかりません</h1>
            <p>公開状態が変更された可能性があります。</p>
          </div>
        ) : (
          <>
            <header className="day-header">
              <p className="eyebrow">
                {entry.source === 'novel' ? 'NOVEL' : 'VRCHAT DIARY'}
              </p>
              <h1 className="day-title">{entry.title}</h1>
              <time className="day-date" dateTime={entry.date}>
                {formatDateOnly(entry.date)}
              </time>
            </header>
            {entry.imageUrl ? (
              <div className="day-image-frame">
                <Image
                  src={entry.imageUrl}
                  alt={`${formatDateOnly(entry.date)}の${entry.source === 'novel' ? '小説' : 'VRChat記録'}`}
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
